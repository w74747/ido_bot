# -*- coding: utf-8 -*-
"""
llm_analyzer.py
---------------
يأخذ بيانات مشروع خام، يرسلها مع الـ System Prompt إلى مزوّد LLM
(Together AI أو DeepSeek، كلاهما متوافق مع شكل Chat Completions
المعروف من OpenAI)، ويرجع نص التحليل كما رد به الموديل.
"""

import json
import logging
import requests

from config import (
    LLM_PROVIDER,
    TOGETHER_API_KEY, TOGETHER_MODEL,
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL,
)
from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


def analyze_project(project: dict) -> str:
    """
    يبني رسالة المستخدم من بيانات المشروع، يستدعي مزوّد الـ LLM المختار،
    ويرجع النص الناتج (سواء كان تقرير كامل أو كلمة "تجاهل").
    """
    user_message = _build_user_message(project)

    if LLM_PROVIDER == "together":
        return _call_together(user_message)
    elif LLM_PROVIDER == "deepseek":
        return _call_deepseek(user_message)
    else:
        raise ValueError(f"مزوّد LLM غير معروف: {LLM_PROVIDER}")


def _build_user_message(project: dict) -> str:
    """
    يحوّل قاموس المشروع إلى نص واضح ومنسّق يُرسل للموديل كرسالة "user"،
    بحيث يحتوي كل المعلومات المتاحة دون حشو زائد.

    يوضّح أيضاً "مرحلة" المشروع (IDO رسمي مُعلن عبر CryptoRank/CoinMarketCap،
    أو جولة تمويل مبكرة جداً عبر RootData/DefiLlama لم تصل بعد لمرحلة
    الطرح العام)، حتى يضبط النموذج توقعاته بخصوص نوع البيانات المتاحة
    ولا يتوقع وجود تفاصيل IDO (مثل تاريخ TGE) في مشروع لا يزال في طور
    التمويل الأولي فقط.
    """
    source = project.get("source", "غير محدد")

    stage_label = {
        "cryptorank": "مشروع IDO/Crowd-sale مُعلن رسمياً (المصدر الرئيسي: CryptoRank)",
        "coinmarketcap": "مشروع IDO/إطلاق مُعلن (مصدر تكميلي: CoinMarketCap)",
        "rootdata": "جولة تمويل مبكرة جداً قبل أي طرح عام (مصدر: RootData)",
        "defillama": "جولة تمويل مبكرة جداً قبل أي طرح عام (مصدر: DefiLlama)",
    }.get(source, "مصدر غير محدد")

    return (
        f"بيانات المشروع التالية وصلت من مصدر بيانات Web3، وهي بمرحلة:\n"
        f"({stage_label})\n"
        "قم بتطبيق المعايير المطلوبة عليها. إذا كانت بيانات المشروع تخص "
        "جولة تمويل مبكرة فقط (بدون تفاصيل IDO رسمية بعد)، حلّل القيمة "
        "الاستثمارية والشرعية بناءً على طبيعة المشروع ونوع التمويل المتاح، "
        "واعتبر 'هدف التخارج' مرتبطاً بمراحل لاحقة متوقعة (مثل أول طرح عام "
        "IDO أو فتح الاستثمار للجمهور) بدل أحداث TGE الفعلية إن لم تتوفر.\n\n"
        f"اسم المشروع: {project.get('name', 'غير معروف')}\n"
        f"الشبكة/المنصة: {project.get('network', 'غير محدد')}\n"
        f"التصنيف كما ورد من المصدر: {project.get('category', 'غير محدد')}\n"
        f"تاريخ الإطلاق/التمويل: {project.get('launch_date', 'غير محدد')}\n"
        f"الوصف الخام: {project.get('description', 'لا يوجد وصف متاح')}\n\n"
        "البيانات الخام الكاملة (JSON) للرجوع إليها إن احتجت تفاصيل إضافية:\n"
        f"{json.dumps(project.get('raw', {}), ensure_ascii=False)[:3000]}"
    )


def _call_together(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }

    try:
        response = requests.post(TOGETHER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError) as e:
        logger.error(f"فشل استدعاء Together AI: {e}")
        return ""


def _call_deepseek(user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError) as e:
        logger.error(f"فشل استدعاء DeepSeek: {e}")
        return ""
