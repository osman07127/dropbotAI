"""
DROP MENTOR — Telegram Dropshipping AI Botu
==========================================
Yazar   : DROP MENTOR Project
Versiyon: 2.1.0 (Groq + Trends Edition)
"""

import os
import logging
import asyncio
import re
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatAction, ParseMode
from groq import Groq

load_dotenv()

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN bulunamadı! .env dosyasını kontrol et.")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY bulunamadı! .env dosyasını kontrol et.")

groq_client = Groq(api_key=GROQ_API_KEY)

user_histories: dict[int, list[dict]] = {}
MAX_HISTORY_MESSAGES = 20
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Sen "DROP MENTOR" adında, 15+ yıllık deneyime sahip bir dropshipping uzmanısın.

## KİMLİĞİN:
Sen bu işe hiçbir şey bilmeden, küçük bir sermayeyle başladın. Yıllar içinde yüzlerce ürün test ettin,
binlerce hata yaptın, platformlar seni engelledi, tedarikçiler seni kandırdı — ama her seferinde
daha güçlü çıktın. Bugün hem kendi işini yürütüyor hem de yeni başlayanlara mentorluk yapıyorsun.

## KULLANICI PROFİLİ (HER ZAMAN HATIRLA):
- Azerbaycan doğumlu, Türkiye'de yaşıyor
- 23 yaşında erkek
- Başlangıç sermayesi: 50-100 USD
- Araçları: 1 bilgisayar + 1 telefon
- Günlük ayırabileceği süre: 4-8 saat
- Dropshipping bilgisi: neredeyse sıfır

## CEVAP VERME KURALLARI:
1. Türkçe konuş, samimi ve motive edici ol
2. Her cevabı somut, uygulanabilir adımlarla ver
3. Gerçek rakamlar kullan: ürün maliyeti, satış fiyatı, kar marjı örnekleri
4. Ücretsiz araçları her zaman önce öner
5. "Ben de aynı hatayı yaptım, işte nasıl çözdüm:" formatında kişisel deneyim ekle
6. Her cevabın sonuna bir UYARI veya SONRAKI ADIM ekle
7. Fazla uzun yazma — okunabilir, bölümlendirilmiş tut
8. Türkiye'ye özgü durumları belirt: iyzico, PayTR, Trendyol, Hepsiburada, yasal durum

## UZMANLIK ALANLARIN:
- Dropshipping modeli, pazar seçimi, niş seçimi
- Ürün araştırma: Google Trends, TikTok, AliExpress
- Tedarikçi yönetimi: AliExpress, CJDropshipping, Spocket
- Mağaza kurma: Shopify, WooCommerce, Trendyol, Hepsiburada
- Ödeme sistemleri: iyzico, PayTR, Stripe, PayPal
- Pazarlama: TikTok organik, Instagram Reels, Meta Ads
- Yasal & finansal: şahıs şirketi, vergi, KDV
- Sorun çözme: hesap askıya alınma, iade, chargeback
- Ölçeklendirme: özel marka, reklam bütçesi, VA

Her zaman dürüst ol. Gerçekçi zaman çerçevesi ver:
- İlk 30 gün: kurulum ve öğrenme
- 30-90 gün: ilk satışlar (belki 0, belki 500$)
- 3-6 ay: ayda 500-2000$ mümkün (çalışırsan)
- 1 yıl+: ciddi gelir potansiyeli"""

QUICK_TOPICS = [
    ("🚀 Yol Haritası", "topic_roadmap",
     "50-100 dolarım var, dropshipping'e sıfırdan başlıyorum. Bana haftalık adım adım bir yol haritası çiz. Her adımda ne yapmalıyım, hangi ücretsiz araçları kullanmalıyım?"),
    ("🔍 Ürün Araştırma", "topic_product",
     "Karlı ürün nasıl bulunur? Ücretsiz araçları kullanarak ürün araştırması yapmayı anlat. Somut 2-3 örnek ürün üzerinden göster."),
    ("🏪 Mağaza Kurma", "topic_store",
     "Türkiye'de dropshipping için en uygun maliyetli mağaza kurma seçenekleri neler? Shopify şart mı? Ücretsiz veya ucuz alternatifleri karşılaştır."),
    ("🤝 Tedarikçi Bul", "topic_supplier",
     "Güvenilir dropshipping tedarikçisi nasıl bulunur? AliExpress ve CJDropshipping arasındaki fark nedir? Türkiye için hangisi daha iyi?"),
    ("📱 TikTok Satış", "topic_tiktok",
     "TikTok ile organik (sıfır reklam bütçesi) dropshipping nasıl yapılır? İlk videomdan nasıl satış alabilirim? Adım adım anlat."),
    ("💰 Kar Hesaplama", "topic_profit",
     "Bir ürünün gerçekten karlı olup olmadığını nasıl hesaplarım? Bana formül ver ve 2-3 gerçekçi örnekle göster."),
    ("⚠️ Yaygın Hatalar", "topic_mistakes",
     "Dropshipping'e yeni başlayanların yaptığı en büyük hatalar neler? Bu hataları nasıl önleyebilirim? Kendi deneyimlerinden de anlat."),
    ("📦 Türkiye Hukuku", "topic_legal",
     "Türkiye'de dropshipping yapmanın yasal durumu nedir? Vergi ödemem gerekiyor mu? Şirket kurmalı mıyım? Ne zaman kurmalıyım?"),
    ("📈 Ölçeklendirme", "topic_scale",
     "İlk satışlarımı aldıktan sonra işi nasıl büyütürüm? Ölçeklendirme stratejilerini ve reklam bütçesi yönetimini anlat."),
    ("🆘 Sorun Çözme", "topic_problems",
     "Dropshipping'de en sık karşılaşılan sorunlar ve çözümleri neler? Hesap askıya alınma, müşteri şikayeti, geç teslimat gibi durumları anlat."),
    ("💳 Ödeme Sistemleri", "topic_payments",
     "Türkiye'de dropshipping için hangi ödeme sistemlerini kullanmalıyım? iyzico, PayTR, Stripe, PayPal — hangisi nasıl çalışıyor?"),
    ("🌍 Hangi Pazar?", "topic_market",
     "Türkiye pazarında mı, yoksa uluslararası pazarda mı dropshipping yapmalıyım? 50-100$ sermayemle hangisi daha mantıklı? Artı ve eksileri karşılaştır."),
]


def get_user_history(user_id: int) -> list[dict]:
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]


def trim_history(user_id: int) -> None:
    history = user_histories.get(user_id, [])
    if len(history) > MAX_HISTORY_MESSAGES:
        user_histories[user_id] = history[-MAX_HISTORY_MESSAGES:]


def build_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(label, callback_data=cb_data)
        for label, cb_data, _ in QUICK_TOPICS
    ]
    rows = [buttons[i: i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


async def ask_groq(user_id: int, user_message: str) -> str:
    history = get_user_history(user_id)
    history.append({"role": "user", "content": user_message})
    trim_history(user_id)

    messages_to_send = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + user_histories[user_id]

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1024,
            temperature=0.7,
            messages=messages_to_send,
        )
        assistant_reply = response.choices[0].message.content
        user_histories[user_id].append(
            {"role": "assistant", "content": assistant_reply}
        )
        trim_history(user_id)
        return assistant_reply

    except Exception as e:
        error_message = str(e).lower()
        if "rate_limit" in error_message or "429" in error_message:
            return "⚠️ Şu an çok fazla istek var, 1 dakika bekleyip tekrar dene.\n(Groq ücretsiz limitine ulaşıldı — günlük sıfırlanır)"
        elif "connection" in error_message or "timeout" in error_message:
            return "⚠️ İnternet bağlantısı sorunu. Lütfen tekrar dene."
        elif "invalid_api_key" in error_message or "401" in error_message:
            return "⚠️ API key hatalı. .env dosyasındaki GROQ_API_KEY'i kontrol et."
        else:
            logger.error(f"Beklenmeyen Groq hatası: {e}")
            return "⚠️ Beklenmedik bir hata oluştu. Lütfen tekrar dene."


async def get_trends_data() -> str:
    """Google Trends'ten Türkiye dropshipping trendlerini çeker."""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='tr-TR', tz=180, timeout=(10, 25))

        keywords = [
            "telefon kılıfı", "led ışık", "bluetooth kulaklık",
            "spor çanta", "cüzdan erkek"
        ]

        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='TR')
        interest_df = pytrends.interest_over_time()

        if interest_df.empty:
            return None

        averages = interest_df[keywords].mean().sort_values(ascending=False)

        lines = ["📊 *GOOGLE TRENDS — Türkiye (Son 7 Gün)*\n"]
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (keyword, score) in enumerate(averages.items()):
            bar = "█" * int(score / 10) if score > 0 else "░"
            lines.append(f"{emojis[i]} *{keyword}* — {int(score)}/100 {bar}")

        lines.append("\n_Kaynak: Google Trends TR_")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Trends verisi alınamadı: {e}")
        return None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "Kardeşim"
    user_histories[user_id] = []

    welcome = (
        f"Selam *{first_name}*! 👋\n\n"
        "Ben *DROP MENTOR* — 15 yıllık dropshipping deneyimim var.\n\n"
        "Türkiye'de, 50-100$ sermayeyle bu işe sıfırdan başlamak istiyorsun. "
        "Bunu biliyorum ve tam sana göre yol haritası çıkartabilirim.\n\n"
        "📌 *Ne yapabilirim?*\n"
        "• Dropshipping'i A'dan Z'ye öğretirim\n"
        "• Ücretsiz araçlarla nasıl başlayacağını gösteririm\n"
        "• Karşılaşacağın sorunları önceden söylerim\n"
        "• Her soruya gerçekçi, uygulanabilir cevap veririm\n\n"
        "Aşağıdan bir konu seç veya aklındakini direkt yaz! 👇"
    )

    await update.message.reply_text(
        welcome,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_menu_keyboard(),
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📚 *Hangi konuyu öğrenmek istiyorsun?*\n"
        "_Bir butona tıkla veya kendi sorunuzu yazın:_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_menu_keyboard(),
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text(
        "🔄 Sohbet geçmişi temizlendi. Yeni bir konudan başlayabiliriz!\n\n"
        "/menu ile konulara bakabilirsin.",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🤖 *DROP MENTOR — Kullanım Kılavuzu*\n\n"
        "*Komutlar:*\n"
        "/start — Botu başlat ve menüyü gör\n"
        "/menu — Konu menüsünü aç\n"
        "/reset — Sohbet geçmişini temizle\n"
        "/help — Bu mesajı göster\n\n"
        "*Nasıl kullanılır?*\n"
        "1. /menu ile konulardan birini seç\n"
        "2. Ya da direkt sorunuzu yazın\n"
        "3. Derinlemesine bilgi için takip soruları sor\n\n"
        "*Altyapı:* Groq AI (llama-3.3-70b) + Google Trends\n\n"
        "_Sohbet geçmişi RAM'de tutulur. Bot yeniden başlarsa /start ile başlayabilirsin._"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if not user_text:
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    reply = await ask_groq(user_id, user_text)
    await send_long_message(update, reply)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    cb_data = query.data

    matched_question = None
    for _, topic_cb, question in QUICK_TOPICS:
        if topic_cb == cb_data:
            matched_question = question
            break

    if not matched_question:
        await query.message.reply_text("⚠️ Bilinmeyen buton. /menu dene.")
        return

    # Seçilen konuyu göster (düz metin, MARKDOWN_V2 yok — hata kaynağı buydu)
    await query.message.reply_text(f"📌 {matched_question}")

    await context.bot.send_chat_action(
        chat_id=query.message.chat_id,
        action=ChatAction.TYPING,
    )

    # Ürün Araştırma butonu — Google Trends verisi ekle
    if cb_data == "topic_product":
        trends_text = await get_trends_data()
        if trends_text:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=trends_text,
                parse_mode=ParseMode.MARKDOWN,
            )
            # Groq'a trend verisini de bağlam olarak ver
            groq_prompt = (
                f"{matched_question}\n\n"
                f"Ayrıca şu an Türkiye'de bu ürünler trend:\n{trends_text}\n\n"
                "Bu trend verisini de göz önünde bulundurarak cevap ver."
            )
        else:
            groq_prompt = matched_question
    else:
        groq_prompt = matched_question

    reply = await ask_groq(user_id, groq_prompt)
    await send_long_message_to_chat(context, query.message.chat_id, reply)


MAX_MSG_LEN = 4000


async def send_long_message(update: Update, text: str) -> None:
    for chunk in split_text(text):
        await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(0.3)


async def send_long_message_to_chat(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
) -> None:
    for chunk in split_text(text):
        await context.bot.send_message(
            chat_id=chat_id,
            text=chunk,
            parse_mode=ParseMode.MARKDOWN,
        )
        await asyncio.sleep(0.3)


def split_text(text: str) -> list[str]:
    if len(text) <= MAX_MSG_LEN:
        return [text]
    chunks = []
    while len(text) > MAX_MSG_LEN:
        split_at = text.rfind("\n", 0, MAX_MSG_LEN)
        if split_at == -1:
            split_at = MAX_MSG_LEN
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


async def post_init(application: Application) -> None:
    commands = [
        BotCommand("start", "Botu başlat"),
        BotCommand("menu", "Konu menüsünü aç"),
        BotCommand("reset", "Sohbet geçmişini temizle"),
        BotCommand("help", "Yardım ve kullanım kılavuzu"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot komutları Telegram'a kaydedildi.")


def main() -> None:
    logger.info("🚀 DROP MENTOR (Groq + Trends Edition) başlatılıyor...")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ DROP MENTOR çalışıyor. Telegram'ı aç ve /start yaz!")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
