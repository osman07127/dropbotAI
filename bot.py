"""
DROP MENTOR — Telegram Dropshipping AI Botu
==========================================
Yazar   : DROP MENTOR Project
Versiyon: 2.0.0 (Groq Edition)
Açıklama: 15 yıllık dropshipping deneyimini simüle eden,
          Groq AI ile güçlendirilmiş Telegram botu.
          Groq ücretsiz planı: 14.400 istek/gün (günlük sıfırlanır)
"""

import os
import logging
import asyncio
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

# ─────────────────────────────────────────────
# BAŞLANGIÇ AYARLARI
# ─────────────────────────────────────────────

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

# Her kullanıcı için sohbet geçmişi RAM'de tutulur
# Format: { user_id: [ {"role": "user"/"assistant", "content": "..."}, ... ] }
user_histories: dict[int, list[dict]] = {}

# Kullanıcı başına maksimum mesaj sayısı (token limitini aşmamak için)
MAX_HISTORY_MESSAGES = 20


# ─────────────────────────────────────────────
# GROQ MODEL SEÇENEKLERİ
# ─────────────────────────────────────────────
# Ücretsiz planda mevcut en iyi modeller:
# - llama-3.3-70b-versatile : En zeki, genel amaçlı (önerilen)
# - llama-3.1-8b-instant    : Daha hızlı ama daha basit
# - mixtral-8x7b-32768      : Uzun bağlam desteği (32k token)
# - gemma2-9b-it            : Hızlı ve ücretsiz alternatif

GROQ_MODEL = "llama-3.3-70b-versatile"


# ─────────────────────────────────────────────
# CLAUDE SİSTEM PROMPTU
# ─────────────────────────────────────────────

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

**Temel Konular:**
- Dropshipping modeli, iş mantığı, avantaj/dezavantajlar
- Pazar seçimi: Türkiye pazarı vs. uluslararası pazar
- Niş seçimi ve rekabet analizi

**Ürün Araştırma:**
- Google Trends, TikTok For You, AliExpress Best Sellers
- Minea, Zendrop, Sell The Trend (ücretsiz sürümleri)
- "Winning product" kriterleri: problem çözme, WOW faktörü, düşük rekabet
- Sezonsal ürünler vs. evergreen ürünler

**Tedarikçi Yönetimi:**
- AliExpress: nasıl seçilir, güvenilir satıcı kriterleri, ePacket kargo
- CJDropshipping: AliExpress'ten farkı, avantajları (Türkiye deposu var!)
- Spocket: Avrupa/ABD tedarikçiler, hızlı teslimat
- Yerel Türk toptancılar: Merter, Laleli, B2B platformları
- Tedarikçiyle müzakere taktikleri

**Mağaza Kurma:**
- Shopify (14 gün ücretsiz, sonra aylık ~30$)
- WooCommerce + WordPress (domain + hosting ~30$/yıl, çok daha ucuz)
- Trendyol, Hepsiburada, N11 (komisyon bazlı, Türkiye pazarı için ideal)
- Etsy (el yapımı/vintage, uluslararası pazar)
- eBay, Amazon (daha zor ama büyük pazar)

**Ödeme Sistemleri (Türkiye):**
- iyzico: en kolay Türk çözümü
- PayTR: iyzico alternatifi
- Stripe: uluslararası (Türkiye'de doğrudan yok ama çözüm yolları var)
- PayPal: personal hesapla başlangıç yapılabilir

**Pazarlama (Ücretsiz/Düşük Bütçeli):**
- TikTok organik: ürün videoları, "POV" formatı, trend ses
- Instagram Reels: benzer format
- Facebook Groups: nişe özel gruplarda paylaşım
- Pinterest: uzun vadeli organik trafik
- Google Shopping Feed (ücretsiz listeleme)
- Influencer ile takas anlaşması (ürün karşılığı tanıtım)
- Ücretli reklamlar: Meta Ads (günde 5$'dan başlayan test bütçesi)

**Operasyon & Lojistik:**
- Sipariş karşılama süreci otomasyonu (DSers, AutoDS)
- Kargo takip numarası yönetimi
- Müşteri hizmetleri şablonları
- İade/değişim politikası oluşturma

**Yasal & Finansal (Türkiye):**
- Şahıs şirketi kurma (en ucuz: ~500-1000 TL)
- E-ticaret vergi durumu
- KDV yükümlülükleri
- Yabancı platformlardan gelir beyanı
- IBAN vs. kurumsal hesap

**Sorun Çözme:**
- PayPal/Stripe hesap askıya alınması
- AliExpress tedarikçi problemi
- Ürün geç geldiğinde müşteri yönetimi
- Chargeback (ödeme iadesi) koruması
- Kötü yorum yönetimi

**Ölçeklendirme:**
- İlk 1000$'dan sonra ne yapmalı
- Özel marka (private label) geçişi
- Reklam bütçesi ölçeklendirme
- VA (sanal asistan) tutma
- Birden fazla mağaza yönetimi

Her zaman dürüst ol. "Bu kolay para" deme. Gerçekçi zaman çerçevesi ver:
- İlk 30 gün: kurulum ve öğrenme
- 30-90 gün: ilk satışlar (belki 0, belki 500$)
- 3-6 ay: ayda 500-2000$ mümkün (çalışırsan)
- 1 yıl+: ciddi gelir potansiyeli"""


# ─────────────────────────────────────────────
# HIZLI KONU MENÜLERİ
# ─────────────────────────────────────────────

# Her tuple: (buton_etiketi, callback_data, kullanıcıya_gönderilecek_soru)
QUICK_TOPICS = [
    (
        "🚀 Yol Haritası",
        "topic_roadmap",
        "50-100 dolarım var, dropshipping'e sıfırdan başlıyorum. Bana haftalık adım adım bir yol haritası çiz. Her adımda ne yapmalıyım, hangi ücretsiz araçları kullanmalıyım?",
    ),
    (
        "🔍 Ürün Araştırma",
        "topic_product",
        "Karlı ürün nasıl bulunur? Ücretsiz araçları kullanarak ürün araştırması yapmayı anlat. Somut 2-3 örnek ürün üzerinden göster.",
    ),
    (
        "🏪 Mağaza Kurma",
        "topic_store",
        "Türkiye'de dropshipping için en uygun maliyetli mağaza kurma seçenekleri neler? Shopify şart mı? Ücretsiz veya ucuz alternatifleri karşılaştır.",
    ),
    (
        "🤝 Tedarikçi Bul",
        "topic_supplier",
        "Güvenilir dropshipping tedarikçisi nasıl bulunur? AliExpress ve CJDropshipping arasındaki fark nedir? Türkiye için hangisi daha iyi?",
    ),
    (
        "📱 TikTok Satış",
        "topic_tiktok",
        "TikTok ile organik (sıfır reklam bütçesi) dropshipping nasıl yapılır? İlk videomdan nasıl satış alabilirim? Adım adım anlat.",
    ),
    (
        "💰 Kar Hesaplama",
        "topic_profit",
        "Bir ürünün gerçekten karlı olup olmadığını nasıl hesaplarım? Bana formül ver ve 2-3 gerçekçi örnekle göster.",
    ),
    (
        "⚠️ Yaygın Hatalar",
        "topic_mistakes",
        "Dropshipping'e yeni başlayanların yaptığı en büyük hatalar neler? Bu hataları nasıl önleyebilirim? Kendi deneyimlerinden de anlat.",
    ),
    (
        "📦 Türkiye Hukuku",
        "topic_legal",
        "Türkiye'de dropshipping yapmanın yasal durumu nedir? Vergi ödemem gerekiyor mu? Şirket kurmalı mıyım? Ne zaman kurmalıyım?",
    ),
    (
        "📈 Ölçeklendirme",
        "topic_scale",
        "İlk satışlarımı aldıktan sonra işi nasıl büyütürüm? Ölçeklendirme stratejilerini ve reklam bütçesi yönetimini anlat.",
    ),
    (
        "🆘 Sorun Çözme",
        "topic_problems",
        "Dropshipping'de en sık karşılaşılan sorunlar ve çözümleri neler? Hesap askıya alınma, müşteri şikayeti, geç teslimat gibi durumları anlat.",
    ),
    (
        "💳 Ödeme Sistemleri",
        "topic_payments",
        "Türkiye'de dropshipping için hangi ödeme sistemlerini kullanmalıyım? iyzico, PayTR, Stripe, PayPal — hangisi nasıl çalışıyor?",
    ),
    (
        "🌍 Hangi Pazar?",
        "topic_market",
        "Türkiye pazarında mı, yoksa uluslararası pazarda mı dropshipping yapmalıyım? 50-100$ sermayemle hangisi daha mantıklı? Artı ve eksileri karşılaştır.",
    ),
]


# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def get_user_history(user_id: int) -> list[dict]:
    """Kullanıcının sohbet geçmişini döndürür, yoksa boş liste oluşturur."""
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]


def trim_history(user_id: int) -> None:
    """Geçmişi MAX_HISTORY_MESSAGES mesajla sınırlar (en sonları tutar)."""
    history = user_histories.get(user_id, [])
    if len(history) > MAX_HISTORY_MESSAGES:
        user_histories[user_id] = history[-MAX_HISTORY_MESSAGES:]


def build_menu_keyboard() -> InlineKeyboardMarkup:
    """Hızlı konu butonlarından oluşan inline klavye oluşturur (2 sütun)."""
    buttons = [
        InlineKeyboardButton(label, callback_data=cb_data)
        for label, cb_data, _ in QUICK_TOPICS
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


async def ask_groq(user_id: int, user_message: str) -> str:
    """
    Groq API'ye istek atar ve cevabı string olarak döndürür.
    Kullanıcının sohbet geçmişini bağlam olarak ekler.
    Groq, OpenAI uyumlu format kullanır: system mesajı ayrı eklenir.
    """
    history = get_user_history(user_id)
    history.append({"role": "user", "content": user_message})
    trim_history(user_id)

    # Groq'a gönderilecek tam mesaj listesi:
    # sistem mesajı + kullanıcı/asistan geçmişi
    messages_to_send = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + user_histories[user_id]

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=1024,
            temperature=0.7,      # Yaratıcılık dengesi (0=robotik, 1=çok serbest)
            messages=messages_to_send,
        )
        assistant_reply = response.choices[0].message.content

        # Asistan cevabını da geçmişe ekle
        user_histories[user_id].append(
            {"role": "assistant", "content": assistant_reply}
        )
        trim_history(user_id)

        return assistant_reply

    except Exception as e:
        error_message = str(e).lower()

        if "rate_limit" in error_message or "429" in error_message:
            logger.warning(f"Groq rate limit aşıldı — kullanıcı: {user_id}")
            return (
                "⚠️ Şu an çok fazla istek var, 1 dakika bekleyip tekrar dene.\n"
                "(Groq ücretsiz limitine ulaşıldı — günlük sıfırlanır)"
            )
        elif "connection" in error_message or "timeout" in error_message:
            logger.error(f"Groq bağlantı hatası: {e}")
            return "⚠️ İnternet bağlantısı sorunu. Lütfen tekrar dene."
        elif "invalid_api_key" in error_message or "401" in error_message:
            logger.error("Groq API key geçersiz!")
            return "⚠️ API key hatalı. .env dosyasındaki GROQ_API_KEY'i kontrol et."
        else:
            logger.error(f"Beklenmeyen Groq hatası: {e}")
            return "⚠️ Beklenmedik bir hata oluştu. Lütfen tekrar dene."


# ─────────────────────────────────────────────
# KOMUT İŞLEYİCİLER
# ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start komutu — hoş geldin mesajı ve menü."""
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "Kardeşim"

    # Geçmişi sıfırla (yeni başlangıç)
    user_histories[user_id] = []

    welcome = (
        f"Selam *{first_name}*\\! 👋\n\n"
        "Ben *DROP MENTOR* — 15 yıllık dropshipping deneyimim var\\.\n\n"
        "Türkiye'de, 50\\-100\\$ sermayeyle bu işe sıfırdan başlamak istiyorsun\\. "
        "Bunu biliyorum ve tam sana göre yol haritası çıkartabilirim\\.\n\n"
        "📌 *Ne yapabilirim\\?*\n"
        "• Dropshipping'i A'dan Z'ye öğretirim\n"
        "• Ücretsiz araçlarla nasıl başlayacağını gösteririm\n"
        "• Karşılaşacağın sorunları önceden söylerim\n"
        "• Her soruya gerçekçi, uygulanabilir cevap veririm\n\n"
        "Aşağıdan bir konu seç veya aklındakini direkt yaz\\! 👇"
    )

    await update.message.reply_text(
        welcome,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=build_menu_keyboard(),
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/menu komutu — konu menüsünü gösterir."""
    await update.message.reply_text(
        "📚 *Hangi konuyu öğrenmek istiyorsun\\?*\n"
        "_Bir butona tıkla veya kendi sorunuzu yazın:_",
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=build_menu_keyboard(),
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reset komutu — sohbet geçmişini temizler."""
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text(
        "🔄 Sohbet geçmişi temizlendi\\. Yeni bir konudan başlayabiliriz\\!\n\n"
        "/menu ile konulara bakabilirsin\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help komutu — kullanım kılavuzu."""
    help_text = (
        "🤖 *DROP MENTOR — Kullanım Kılavuzu*\n\n"
        "*Komutlar:*\n"
        "/start — Botu başlat ve menüyü gör\n"
        "/menu — Konu menüsünü aç\n"
        "/reset — Sohbet geçmişini temizle\n"
        "/help — Bu mesajı göster\n\n"
        "*Nasıl kullanılır\\?*\n"
        "1\\. /menu ile konulardan birini seç\n"
        "2\\. Ya da direkt sorunuzu yazın\n"
        "3\\. Derinlemesine bilgi için takip soruları sor\n\n"
        "*Altyapı:* Groq AI \\(llama\\-3\\.3\\-70b\\) • Ücretsiz\n\n"
        "_Sohbet geçmişi RAM'de tutulur\\. "
        "Bot yeniden başlarsa /start ile başlayabilirsin\\._"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN_V2)


# ─────────────────────────────────────────────
# MESAJ İŞLEYİCİLER
# ─────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıdan gelen her normal metin mesajını işler."""
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if not user_text:
        return

    # "Yazıyor..." göstergesi
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    # Groq'tan cevap al
    reply = await ask_groq(user_id, user_text)

    # Telegram'da maksimum mesaj uzunluğu 4096 karakter
    # Uzun cevapları parçalara böl
    await send_long_message(update, reply)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inline klavye butonlarına basıldığında çalışır."""
    query = update.callback_query
    await query.answer()  # Butondaki yüklenme animasyonunu durdur

    user_id = query.from_user.id
    cb_data = query.data

    # Callback verisiyle eşleşen konuyu bul
    matched_question = None
    for _, topic_cb, question in QUICK_TOPICS:
        if topic_cb == cb_data:
            matched_question = question
            break

    if not matched_question:
        await query.message.reply_text("⚠️ Bilinmeyen buton. /menu dene.")
        return

    # Kullanıcının seçtiği konuyu mesaj olarak göster
    await query.message.reply_text(
        f"📌 _{matched_question}_",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    # "Yazıyor..." göstergesi
    await context.bot.send_chat_action(
        chat_id=query.message.chat_id,
        action=ChatAction.TYPING,
    )

    # Groq'tan cevap al
    reply = await ask_groq(user_id, matched_question)
    await send_long_message_to_chat(context, query.message.chat_id, reply)


# ─────────────────────────────────────────────
# UZUN MESAJ GÖNDERME YARDIMCILARI
# ─────────────────────────────────────────────

MAX_MSG_LEN = 4000  # Telegram limiti 4096, biraz pay bırakıyoruz


async def send_long_message(update: Update, text: str) -> None:
    """Çok uzun metinleri parçalara bölerek gönderir."""
    for chunk in split_text(text):
        await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(0.3)


async def send_long_message_to_chat(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
) -> None:
    """Callback handler'dan gelen uzun mesajları gönderir."""
    for chunk in split_text(text):
        await context.bot.send_message(
            chat_id=chat_id,
            text=chunk,
            parse_mode=ParseMode.MARKDOWN,
        )
        await asyncio.sleep(0.3)


def split_text(text: str) -> list[str]:
    """
    Metni Telegram'ın izin verdiği maksimum uzunluğa böler.
    Satır ortasında kesmekten kaçınır.
    """
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


# ─────────────────────────────────────────────
# ANA BAŞLATICI
# ─────────────────────────────────────────────

async def post_init(application: Application) -> None:
    """Bot başladığında komut listesini Telegram'a kaydet."""
    commands = [
        BotCommand("start", "Botu başlat"),
        BotCommand("menu",  "Konu menüsünü aç"),
        BotCommand("reset", "Sohbet geçmişini temizle"),
        BotCommand("help",  "Yardım ve kullanım kılavuzu"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot komutları Telegram'a kaydedildi.")


def main() -> None:
    """Botu başlatır ve mesajları dinlemeye başlar."""
    logger.info("🚀 DROP MENTOR (Groq Edition) başlatılıyor...")
    logger.info(f"   Model: {GROQ_MODEL}")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Komut handler'ları
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu",  cmd_menu))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help",  cmd_help))

    # Inline buton handler'ı
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Normal metin mesajı handler'ı (komutlar hariç)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("✅ DROP MENTOR çalışıyor. Telegram'ı aç ve /start yaz!")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()