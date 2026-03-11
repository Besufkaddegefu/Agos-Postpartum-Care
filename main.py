import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes, ConversationHandler)
from datetime import datetime
import re

# --- CONFIGURATION ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [
    int(os.environ.get("ADMIN_ID_1", "123456789")),  # Primary admin
    int(os.environ.get("ADMIN_ID_2", "987654321")),  # Secondary admin
    int(os.environ.get("ADMIN_ID_3", "555555555"))   # Tertiary admin
]
LOGO_PATH = os.environ.get("LOGO_PATH", "logo.webp")
SERVICES_PDF_PATH = os.environ.get("SERVICES_PDF_PATH", "services_catalog.pdf")

# Working hours configuration (Ethiopian Local Time)
WORKING_HOURS_START = 8  # 8:00 AM LT
WORKING_HOURS_END = 20   # 8:00 PM LT

print("DEBUG - TOKEN is:", repr(TOKEN))
print("DEBUG - Admin IDs:", ADMIN_IDS)

# --- CONVERSATION STATES ---
# Decor Booking States (updated)
(D_NAME, D_GENDER, D_ADDR, D_PHONE, D_USERNAME, D_CONTACT, D_PKG, D_DATE, D_HOUSE, D_PAYMENT, D_NOTES) = range(40, 51)

# Limousine Booking States
(L_NAME, L_PHONE, L_DATE, L_ADDR, L_PACKAGE, L_PAYMENT) = range(60, 66)

# Photography Booking States
(PH_NAME, PH_PHONE, PH_DATE, PH_ADDR, PH_PACKAGE, PH_PAYMENT) = range(70, 76)

# --- WORKING HOURS CHECK ---
def is_within_working_hours():
    """Check if current time is within working hours (8 AM - 8 PM LT)"""
    current_hour = datetime.now().hour
    return WORKING_HOURS_START <= current_hour < WORKING_HOURS_END

async def working_hours_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display working hours message before proceeding"""
    working_msg = (
        "⏰ *Working Hours & Contact*\n\n"
        "Please note that AGOS Postpartum Care does not accept calls after 2:00 PM (local time).\n"
        "If you contact us after this time, kindly leave your message here and our team will review it and contact you the next morning.\n\n"
        "⏰ *የስራ ሰዓታችን*\n\n"
        "እባክዎ ያስታውሱ፤ AGOS Postpartum Care ከምሽቱ 2:00 ሰዓት በኋላ ጥሪ አይቀበልም።\n"
        "ከዚህ ሰዓት በኋላ ቦታ ለማስያዝ እባክዎ መልእክትዎን በዚህ ፕላትፎርም ይተዉ፣ ቡድናችንም በሚቀጥለው ጠዋት ያገኞዎታል።"
    )
    
    keyboard = [[InlineKeyboardButton("Continue / ቀጥል", callback_data='after_hours')]]
    
    if update.message:
        await update.message.reply_text(working_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.callback_query.message.reply_text(working_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    return ConversationHandler.END

# --- CONTENT ---
CONTENT = {
    'en': {
        'welcome': (
            "🎁 *Welcome to AGOS Decor & Special Services* 🌸\n\n"
            "✨ Premium home decor for your special moments\n"
            "🚗 Luxury limousine arrivals\n"
            "📸 Professional photography & videography\n\n"
            "🌐 www.agospostpartumcare.com\n\n"
            "_Making your celebrations unforgettable._"
        ),
        'btns': ["🎁 Decor Packages", "🚗 Limousine Service", "📸 Media Services", "📞 Contact Us", "📋 Services Catalog", "🎁 Book Decor", "🚗 Book Limousine", "📸 Book Media"],
        'decor_text': (
            "🎁 *Home Decor Packages*\n"
            "__________________________\n\n"
            "🔸 **Home Decor (15,000 ETB)**\n\n"
            "• Bedroom Decoration\n\n"
            "• Floor Decoration\n\n"
            "• Corridor Decoration\n\n"
            "• Salon Decoration\n\n"
            "📱 *See our work:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/decor)\n\n"
            "__________________________\n\n"
            "💎 **Home Decor Deluxe (20,000 ETB)**\n\n"
            "• Bedroom, Corridor & Salon Decor\n\n"
            "• Large Flower Arrangement (Bouquet + Floor) - እቅፍ አበባ\n\n"
            "• 2 Kg Normal Cake\n\n"
            "📱 *See our work:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/decor)\n\n"
            "__________________________\n\n"
            "👑 **Home Decor Premium (25,000 ETB)**\n\n"
            "• Bedroom Decor with Agober rent (2 weeks)\n\n"
            "• Corridor & Salon Decor\n\n"
            "• Large Flower Arrangement (Bouquet + Floor) - እቅፍ አበባ\n\n"
            "• 2 Kg Custom Made Cake - 2 ኪሎ ኬክ በመረጡት ዲዛይን\n\n"
            "📱 *See our work:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/decor)"
        ),
        'limousine_text': (
            "🚗 *The Grand Arrival - Limousine Service*\n"
            "__________________________\n\n"
            "⭐ **The Grand Arrival (25,000 ETB)**\n\n"
            "• Special limousine service\n\n"
            "• Grand and elegant ride home\n\n"
            "📸 *Check out our arrivals:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum)\n\n"
            "__________________________\n\n"
            "✨ **Special Arrival (30,000 ETB)**\n\n"
            "• Exclusive limousine service\n\n"
            "• Luxurious and heartwarming ride\n\n"
            "__________________________\n\n"
            "👑 **Royal Welcome (35,000 ETB)**\n\n"
            "• Premium luxury limousine\n\n"
            "• Truly regal welcome home"
        ),
        'media_text': (
            "📸 *Photography & Videography Services*\n"
            "__________________________\n\n"
            "📱 **Digital Photography (10,000 ETB)**\n\n"
            "• Professional photography\n\n"
            "• All photos delivered in soft copy\n\n"
            "• (No physical album)\n\n"
            "📸 *See our portfolio:* [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/media)\n\n"
            "__________________________\n\n"
            "🖼️ **Standard Photography (12,000 ETB)**\n\n"
            "• Normal album sized photos (100 printed)\n\n"
            "• Soft copy of all photos\n\n"
            "__________________________\n\n"
            "💎 **Premium Photography (15,000 ETB)**\n\n"
            "• Laminated photo album (20x30 cm)\n\n"
            "• Soft copy of all photos\n\n"
            "__________________________\n\n"
            "🎥 **Videography Package (15,000 ETB)**\n\n"
            "• Full video coverage\n\n"
            "• Edited video (soft copy)"
        ),
        'contact_text': (
            "📞 *Contact Us*\n\n"
            "⏰ *Working Hours:* 8:00 AM - 8:00 PM (Local Time)\n"
            "⚠️ *Note:* Not operational before 2:00 LT / 8:00 PM\n\n"
            "📱 *Telegram:* @agos_postpartumcare\n"
            "📞 *Phone:* +251 967 621 545 | +251 980 040 468\n\n"
            "📸 *Instagram:* [@agospostpartum](https://instagram.com/agospostpartum)\n"
            "🎵 *TikTok:* [@agos_postpartumcare](https://www.tiktok.com/@agos_postpartumcare)\n"
            "🌐 *Website:* [www.agospostpartumcare.com](https://www.agospostpartumcare.com/)\n"
            "📍 *Location:* [Piassa, Abat Commercial](https://maps.google.com/?q=Piassa+Abat+Commercial+Addis+Ababa)\n\n"
            "💬 *Telegram Username:* @agos_postpartumcare"
        ),
        'agree_btn': "I Agree ✅",
        'back': "🔙 Back to Menu",
        'change_lang': "🌍 Change Language / ቋንቋ ቀይር",
        'q_back': "⬅️ Previous Question",
        'discover_more': (
            "✨ *Thank you for your booking!* ✨\n\n"
            "Now that you've chosen your decor package, why not check out our other services?\n\n"
            "🚗 *Limousine Service* - Make a grand entrance\n"
            "📸 *Photography Packages* - Capture every moment\n\n"
            "Click below to explore more!"
        )
    },
    'am': {
        'welcome': (
            "🎁 *እንኳን ወደ AGOS ዲኮር እና ልዩ አገልግሎቶች በሰላም መጡ* 🌸\n\n"
            "✨ ለልዩ ጊዜያቶችዎ የሚሆን ፕሪሚየም የቤት ዲኮር\n"
            "🚗 የሊሙዚን አገልግሎት\n"
            "📸 ፕሮፌሽናል ፎቶግራፍ እና ቪዲዮግራፊ\n\n"
            "🌐 www.agospostpartumcare.com"
        ),
        'btns': ["🎁 የዲኮር ፓኬጆች", "🚗 የሊሙዚን አገልግሎት", "📸 የሚዲያ አገልግሎቶች", "📞 ያግኙን", "📋 የአገልግሎት ካታሎግ", "🎁 ዲኮር ይዘዙ", "🚗 ሊሙዚን ይዘዙ", "📸 ሚዲያ ይዘዙ"],
        'decor_text': (
            "🎁 *የዲኮር ፓኬጆች*\n"
            "__________________________\n\n"
            "🔸 **መደበኛ ዲኮር (15,000 ብር)**\n\n"
            "• የመኝታ ቤት ዲኮር\n\n"
            "• የወለል ዲኮር\n\n"
            "• የኮሪደር ዲኮር\n\n"
            "• የሳሎን ዲኮር\n\n"
            "📱 *ስራዎቻችንን ይመልከቱ:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/decor)\n\n"
            "__________________________\n\n"
            "💎 **ደልክስ ዲኮር (20,000 ብር)**\n\n"
            "• የመኝታ ቤት፣ ኮሪደር እና ሳሎን ዲኮር\n\n"
            "• ትልቅ የአበባ ዝግጅት - እቅፍ አበባ\n\n"
            "• 2 ኪሎ መደበኛ ኬክ\n\n"
            "📱 *ስራዎቻችንን ይመልከቱ:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/decor)\n\n"
            "__________________________\n\n"
            "👑 **ፕሪሚየም ዲኮር (25,000 ብር)**\n\n"
            "• የመኝታ ቤት ዲኮር ከአጎበር ኪራይ ጋር (2 ሳምንት)\n\n"
            "• የኮሪደር እና ሳሎን ዲኮር\n\n"
            "• ትልቅ የአበባ ዝግጅት - እቅፍ አበባ\n\n"
            "• 2 ኪሎ ኬክ በመረጡት ዲዛይን\n\n"
            "📱 *ስራዎቻችንን ይመልከቱ:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/decor)"
        ),
        'limousine_text': (
            "🚗 *የሊሙዚን አገልግሎት*\n"
            "__________________________\n\n"
            "⭐ **መደበኛ አቀባበል (25,000 ብር)**\n\n"
            "• ልዩ የሊሙዚን አገልግሎት\n\n"
            "📸 *አቀባበሎቻችንን ይመልከቱ:* [TikTok](https://www.tiktok.com/@agos_postpartumcare) | [Instagram](https://instagram.com/agospostpartum)\n\n"
            "__________________________\n\n"
            "✨ **ልዩ አቀባበል (30,000 ብር)**\n\n"
            "• ልዩ የሊሙዚን አገልግሎት\n\n"
            "__________________________\n\n"
            "👑 **የሮያል አቀባበል (35,000 ብር)**\n\n"
            "• ፕሪሚየም የሊሙዚን አገልግሎት"
        ),
        'media_text': (
            "📸 *ፎቶ እና ቪዲዮ አገልግሎቶች*\n"
            "__________________________\n\n"
            "📱 **ዲጂታል ፎቶግራፍ (10,000 ብር)**\n\n"
            "• የባለሙያ ፎቶግራፍ አገልግሎት\n\n"
            "📸 *ስራዎቻችንን ይመልከቱ:* [Instagram](https://instagram.com/agospostpartum) | [Website](https://www.agospostpartumcare.com/media)\n\n"
            "__________________________\n\n"
            "🖼️ **መደበኛ ፎቶግራፍ (12,000 ብር)**\n\n"
            "• 100 የታተሙ ፎቶዎች\n\n"
            "__________________________\n\n"
            "💎 **ፕሪሚየም ፎቶግራፍ (15,000 ብር)**\n\n"
            "• ላሚኔት የተደረገ አልበም\n\n"
            "__________________________\n\n"
            "🎥 **የቪዲዮ አገልግሎት (15,000 ብር)**\n\n"
            "• ሙሉ የቪዲዮ ሽፋን"
        ),
        'contact_text': (
            "📞 *ያግኙን*\n\n"
            "⏰ *የስራ ሰዓት:* 8፡00 ጥዋት - 8፡00 ማታ (በአካባቢው ሰዓት)\n"
            "⚠️ *ማሳሰቢያ:* ከምሽቱ 2፡00 / 8፡00 ሰዓት በፊት አይሰራም\n\n"
            "📱 *ቴሌግራም:* @agos_postpartumcare\n"
            "📞 *ስልክ:* +251 967 621 545 | +251 980 040 468\n\n"
            "📸 *ኢንስታግራም:* [@agospostpartum](https://instagram.com/agospostpartum)\n"
            "🎵 *ቲክቶክ:* [@agos_postpartumcare](https://www.tiktok.com/@agos_postpartumcare)\n"
            "🌐 *ዌብሳይት:* [www.agospostpartumcare.com](https://www.agospostpartumcare.com/)\n"
            "📍 *አድራሻ:* [ፒያሳ፣ አባት ኮሜርሻል](https://maps.google.com/?q=Piassa+Abat+Commercial+Addis+Ababa)"
        ),
        'agree_btn': "እስማማለሁ ✅",
        'back': "🔙 ወደ ዋና ማውጫ",
        'change_lang': "🌍 Change Language / ቋንቋ ቀይር",
        'q_back': "⬅️ ወደ ኋላ ተመለስ",
        'discover_more': (
            "✨ *ለትዕዛዝዎ እናመሰግናለን!* ✨\n\n"
            "አሁን የዲኮር ፓኬጅዎን ከመረጡ በኋላ፣ ሌሎች አገልግሎቶቻችንን ለምን አይመለከቱም?\n\n"
            "🚗 *የሊሙዚን አገልግሎት* - በታላቅ አቀባበል ይግቡ\n"
            "📸 *የፎቶግራፍ አገልግሎቶች* - ትዝታዎችን ይቅረጹ\n\n"
            "ለማሰስ ከታች ይጫኑ!"
        )
    }
}

# --- PDF GENERATOR WITH LOGO ---
def create_decor_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add Logo if it exists
    y_start = height - 50
    if os.path.exists(LOGO_PATH):
        try:
            logo = ImageReader(LOGO_PATH)
            c.drawImage(logo, 480, height - 80, width=60, height=60, mask='auto')
        except Exception:
            pass

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "AGOS Decor Booking")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, "Official Decor Order Form")
    c.line(50, height - 85, 550, height - 85)

    # Content
    c.setFont("Helvetica", 11)
    y_position = height - 120

    for key, value in data.items():
        if key.startswith('d_'):
            label = key[2:].replace('_', ' ').upper()
            text = f"{label}: {value}"
            c.drawString(50, y_position, text)
            y_position -= 25
            if y_position < 60:
                c.showPage()
                y_position = height - 50

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 40, "Generated via AGOS Telegram Bot. Awaiting payment confirmation.")
    c.save()
    buffer.seek(0)
    return buffer

# --- HELPERS ---
def get_back_kb(lang):
    return InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back')]])

def get_nav_kb(lang, back_callback='d_back'):
    """Returns keyboard with Back and Menu buttons"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data=back_callback)],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])

async def send_services_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the services catalog PDF"""
    if os.path.exists(SERVICES_PDF_PATH):
        with open(SERVICES_PDF_PATH, 'rb') as pdf_file:
            await update.callback_query.message.reply_document(
                document=pdf_file,
                filename="AGOS_Services_Catalog.pdf",
                caption="📋 Our complete services catalog / ሙሉ የአገልግሎት ካታሎጋችን"
            )
    else:
        await update.callback_query.message.reply_text(
            "PDF catalog will be available soon. / የአገልግሎት ካታሎግ በቅርቡ ይገኛል።"
        )

# --- NAVIGATION ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - shows working hours gate first"""
    context.user_data.clear()
    return await working_hours_gate(update, context)

async def after_hours_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle after acknowledging working hours - show language selection"""
    keyboard = [[InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
                [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='lang_am')]]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "🌿 Choose Language / ቋንቋ ይምረጡ:", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return ConversationHandler.END

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = None):
    """Show main menu after language selection"""
    if lang:
        context.user_data['lang'] = lang
    else:
        lang = context.user_data.get('lang', 'en')

    btns = CONTENT[lang]['btns']
    keyboard = [
        [InlineKeyboardButton(btns[0], callback_data='info_decor'), 
         InlineKeyboardButton(btns[1], callback_data='info_limousine')],
        [InlineKeyboardButton(btns[2], callback_data='info_media'), 
         InlineKeyboardButton(btns[3], callback_data='info_contact')],
        [InlineKeyboardButton(btns[5], callback_data='d_start'), 
         InlineKeyboardButton(btns[6], callback_data='l_start')],
        [InlineKeyboardButton(btns[7], callback_data='ph_start'),
         InlineKeyboardButton(btns[4], callback_data='send_pdf')],
        [InlineKeyboardButton(CONTENT[lang]['change_lang'], callback_data='restart')]
    ]
    
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            CONTENT[lang]['welcome'], 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            CONTENT[lang]['welcome'], 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )

async def info_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle info page callbacks"""
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    choice = query.data.replace('info_', '')
    text = CONTENT[lang].get(f'{choice}_text', "Information coming soon...")
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]])
    await query.message.edit_text(text, reply_markup=back_btn, parse_mode='Markdown')

# --- DECOR BOOKING FLOW (UPDATED) ---
async def d_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start decor booking flow"""
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    await query.answer()
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])
    
    await query.message.reply_text(
        "🎁 **Decor Booking / ዲኮር ለማዘዝ**\n\n1. Full Name / ሙሉ ስም:",
        reply_markup=kb
    )
    return D_NAME

async def d_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input"""
    context.user_data['d_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("Male / ወንድ", callback_data='Male'),
         InlineKeyboardButton("Female / ሴት", callback_data='Female')],
        [InlineKeyboardButton("Not Sure / እርግጠኛ አይደለሁም", callback_data='NotSure')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await update.message.reply_text(
        "2. Gender of the Newborn / የሕፃኑ ጾታ:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return D_GENDER

async def d_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender selection"""
    query = update.callback_query
    await query.answer()
    context.user_data['d_gender'] = query.data
    lang = context.user_data.get('lang', 'en')
    
    await query.message.reply_text(
        "3. House Address for Decor Setup / ዲኮር ለመስራት የቤት አድራሻ:",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_ADDR

async def d_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle address input"""
    context.user_data['d_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Client Phone Number / የደንበኛ ስልክ ቁጥር:",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_PHONE

async def d_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone input"""
    context.user_data['d_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "5. Your Telegram Username (e.g., @username) / የቴሌግራም መለያዎ (ለምሳሌ፡ @username):",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_USERNAME

async def d_step5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Telegram username input"""
    context.user_data['d_username'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "6. Contact Person at Home (if different) / በቤት ውስጥ የሚገኝ የደንበኛ ተወካይ (ከላይ ከተጠቀሰው ሲለይ):",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_CONTACT

async def d_step6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact person input"""
    context.user_data['d_contact'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    # Updated package selection text
    kb = [
        [InlineKeyboardButton("Home Decor - 15,000 ETB / መደበኛ ዲኮር - 15,000 ብር", callback_data='15k')],
        [InlineKeyboardButton("Home Decor Deluxe - 20,000 ETB / ደልክስ ዲኮር - 20,000 ብር", callback_data='20k')],
        [InlineKeyboardButton("Home Decor Premium - 25,000 ETB / ፕሪሚየም ዲኮር - 25,000 ብር", callback_data='25k')],
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await update.message.reply_text(
        "7. Select your preferred Decor Package / የሚፈልጉትን የዲኮር ፓኬጅ ይምረጡ:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return D_PKG

async def d_step7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle package selection"""
    query = update.callback_query
    await query.answer()
    context.user_data['d_pkg'] = query.data
    lang = context.user_data.get('lang', 'en')
    
    # Updated date/time question with new phrasing
    await query.message.reply_text(
        "8. Preferred Date & Time for the Decor setup (e.g., Morning 4:00 AM)\nFormat: (dd/mm/yyyy), (Time)\n\n"
        "8. ዲኮሩን የሚፈልጉበት ቀን እና ሰአት (ለምሳሌ፡ ጥዋት 4፡00)\nቅርጸት: (ቀን/ወር/ዓመት), (ሰዓት)",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_DATE

async def d_step8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date/time input"""
    context.user_data['d_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')

    kb = [
        [InlineKeyboardButton("Villa / ቪላ", callback_data='Villa'),
         InlineKeyboardButton("Apartment / አፓርትመንት", callback_data='Apartment')],
        [InlineKeyboardButton("Condominium / ኮንዶሚየም", callback_data='Condominium')],
        [InlineKeyboardButton("G+1", callback_data='G1'),
         InlineKeyboardButton("G+2", callback_data='G2')],
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]

    await update.message.reply_text(
        "9. House Type / የቤት አይነት:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return D_HOUSE

async def d_step9(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle house type selection"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')

    if query.data == 'd_back':
        return await d_step8(update, context)

    context.user_data['d_house'] = query.data
    
    # Payment warning message
    warning_msg = (
        "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
        "Booking will not be confirmed unless a screenshot of the half-payment is sent.\n"
        "ያስያዙት ቦታ የሚረጋገጠው የግማሽ ክፍያ ስክሪን ሾት ከተላከ በኋላ ብቻ ነው።\n\n"
        "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
        "🏧 *Commercial Bank of Ethiopia (CBE)*\n"
        "👤 Account Name: AGOS POSTPARTUM CARE\n"
        "🔢 Account Number: 10001345678901\n"
        "🌍 Branch: Piassa Branch\n\n"
        "📱 *Tele Birr / ቴሌ ብር*\n"
        "📞 Phone: 0967621545\n"
        "👤 Name: AGOS POSTPARTUM CARE"
    )
    
    await query.message.reply_text(warning_msg, parse_mode='Markdown')
    await query.message.reply_text(
        "10. Special Notes (Limousine, Photo, Video, or None) / ልዩ ማስታወሻ (ሊሙዚን፣ ፎቶ፣ ቪዲዮ፣ ወይም ምንም):",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_NOTES

async def d_step10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notes input"""
    context.user_data['d_notes'] = update.message.text
    lang = context.user_data.get('lang', 'en')

    await update.message.reply_text(
        "📤 Upload your Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_PAYMENT

async def d_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment screenshot and finalize booking"""
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo. / እባክዎ ፎቶ ይላኩ።",
            reply_markup=get_nav_kb(lang, back_callback='d_back')
        )
        return D_PAYMENT

    pay_img = update.message.photo[-1].file_id
    
    # Create PDF
    pdf_file = create_decor_pdf(context.user_data)
    
    summary = (f"🔔 **NEW AGOS DECOR BOOKING / አዲስ የዲኮር ትዕዛዝ** 🔔\n\n"
               f"👤 Name / ስም: {context.user_data.get('d_name')}\n"
               f"👶 Baby Gender / የሕፃኑ ጾታ: {context.user_data.get('d_gender')}\n"
               f"📞 Phone / ስልክ: {context.user_data.get('d_phone')}\n"
               f"📱 Telegram / ቴሌግራም: {context.user_data.get('d_username')}\n"
               f"🏠 Address / አድራሻ: {context.user_data.get('d_addr')}\n"
               f"🏗️ House Type / የቤት አይነት: {context.user_data.get('d_house')}\n"
               f"🎁 Package / ፓኬጅ: {context.user_data.get('d_pkg')}\n"
               f"📅 Date / ቀን: {context.user_data.get('d_date')}\n"
               f"📝 Notes / ማስታወሻ: {context.user_data.get('d_notes')}")

    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=pay_img, caption=summary, parse_mode='Markdown')
            await context.bot.send_document(chat_id=admin_id, document=pdf_file, filename=f"Decor_{context.user_data.get('d_name','Booking')}.pdf")
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")

    # Send confirmation to user with updated status message
    pdf_file.seek(0)
    await update.message.reply_document(
        document=pdf_file, 
        filename="AGOS_Decor_Booking.pdf", 
        caption="✅ Your booking is awaiting confirmation. / ማረጋገጫ በመጠበቅ ላይ።"
    )

    # Show discover more page
    await show_discover_more(update, context)
    
    return ConversationHandler.END

async def show_discover_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show discover more page after successful booking"""
    lang = context.user_data.get('lang', 'en')
    
    discover_kb = [
        [InlineKeyboardButton("🚗 Book Limousine / ሊሙዚን ይዘዙ", callback_data='l_start'),
         InlineKeyboardButton("📸 Book Media / ሚዲያ ይዘዙ", callback_data='ph_start')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await update.message.reply_text(
        CONTENT[lang]['discover_more'],
        reply_markup=InlineKeyboardMarkup(discover_kb),
        parse_mode='Markdown'
    )

async def d_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button in decor flow"""
    query = update.callback_query
    await query.answer()
    # Implement back navigation logic
    return D_NAME  # Default fallback

# --- LIMOUSINE BOOKING FLOW ---
async def l_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start limousine booking flow"""
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    await query.answer()
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])
    
    await query.message.reply_text(
        "🚗 **Limousine Booking / ሊሙዚን ማስያዣ**\n\n1. Full Name / ሙሉ ስም:",
        reply_markup=kb
    )
    return L_NAME

async def l_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle limousine name input"""
    context.user_data['l_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "2. Phone Number / ስልክ ቁጥር:",
        reply_markup=get_nav_kb(lang, back_callback='l_back')
    )
    return L_PHONE

async def l_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle limousine phone input"""
    context.user_data['l_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "3. Preferred Date & Time (e.g., Morning 8:00 AM)\nFormat: (dd/mm/yyyy), (Time)\n\n"
        "3. የሚፈለግ ቀን እና ሰዓት (ለምሳሌ፡ ጥዋት 8፡00)\nቅርጸት: (ቀን/ወር/ዓመት), (ሰዓት)",
        reply_markup=get_nav_kb(lang, back_callback='l_back')
    )
    return L_DATE

async def l_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle limousine date input"""
    context.user_data['l_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Pickup Address / የሚነሱበት አድራሻ:",
        reply_markup=get_nav_kb(lang, back_callback='l_back')
    )
    return L_ADDR

async def l_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle limousine address input"""
    context.user_data['l_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("The Grand Arrival - 25,000 ETB", callback_data='l_25k'),
         InlineKeyboardButton("Special Arrival - 30,000 ETB", callback_data='l_30k')],
        [InlineKeyboardButton("Royal Welcome - 35,000 ETB", callback_data='l_35k')],
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='l_back')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await update.message.reply_text(
        "5. Select Package / ፓኬጅ ይምረጡ:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return L_PACKAGE

async def l_step5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle limousine package selection"""
    query = update.callback_query
    await query.answer()
    context.user_data['l_package'] = query.data
    lang = context.user_data.get('lang', 'en')
    
    # Payment warning
    warning_msg = (
        "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
        "Booking will not be confirmed unless a screenshot of the half-payment is sent.\n"
        "ያስያዙት ቦታ የሚረጋገጠው የግማሽ ክፍያ ስክሪን ሾት ከተላከ በኋላ ብቻ ነው።\n\n"
        "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
        "🏧 *Commercial Bank of Ethiopia (CBE)*\n"
        "👤 Account Name: AGOS POSTPARTUM CARE\n"
        "🔢 Account Number: 10001345678901\n\n"
        "📱 *Tele Birr / ቴሌ ብር*\n"
        "📞 Phone: 0967621545"
    )
    
    await query.message.reply_text(warning_msg, parse_mode='Markdown')
    await query.message.reply_text(
        "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
        reply_markup=get_nav_kb(lang, back_callback='l_back')
    )
    return L_PAYMENT

async def l_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle limousine payment screenshot"""
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo. / እባክዎ ፎቶ ይላኩ።",
            reply_markup=get_nav_kb(lang, back_callback='l_back')
        )
        return L_PAYMENT

    pay_img = update.message.photo[-1].file_id
    
    summary = (f"🔔 **NEW LIMOUSINE BOOKING / አዲስ የሊሙዚን ትዕዛዝ** 🔔\n\n"
               f"👤 Name / ስም: {context.user_data.get('l_name')}\n"
               f"📞 Phone / ስልክ: {context.user_data.get('l_phone')}\n"
               f"📅 Date / ቀን: {context.user_data.get('l_date')}\n"
               f"🏠 Address / አድራሻ: {context.user_data.get('l_addr')}\n"
               f"🎁 Package / ፓኬጅ: {context.user_data.get('l_package')}")

    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=pay_img, caption=summary, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")

    await update.message.reply_text(
        "✅ Your booking is awaiting confirmation. / ማረጋገጫ በመጠበቅ ላይ።"
    )
    
    # Show discover more page
    await show_discover_more(update, context)
    
    return ConversationHandler.END

# --- PHOTOGRAPHY BOOKING FLOW ---
async def ph_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start photography booking flow"""
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    await query.answer()
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])
    
    await query.message.reply_text(
        "📸 **Media Services Booking / የሚዲያ አገልግሎት ማስያዣ**\n\n1. Full Name / ሙሉ ስም:",
        reply_markup=kb
    )
    return PH_NAME

async def ph_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photography name input"""
    context.user_data['ph_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "2. Phone Number / ስልክ ቁጥር:",
        reply_markup=get_nav_kb(lang, back_callback='ph_back')
    )
    return PH_PHONE

async def ph_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photography phone input"""
    context.user_data['ph_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "3. Event Date & Time\nFormat: (dd/mm/yyyy), (Time)\n\n"
        "3. የዝግጅቱ ቀን እና ሰዓት\nቅርጸት: (ቀን/ወር/ዓመት), (ሰዓት)",
        reply_markup=get_nav_kb(lang, back_callback='ph_back')
    )
    return PH_DATE

async def ph_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photography date input"""
    context.user_data['ph_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Event Address / የዝግጅቱ አድራሻ:",
        reply_markup=get_nav_kb(lang, back_callback='ph_back')
    )
    return PH_ADDR

async def ph_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photography address input"""
    context.user_data['ph_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("Digital Photography - 10,000 ETB", callback_data='ph_10k')],
        [InlineKeyboardButton("Standard Photography - 12,000 ETB", callback_data='ph_12k')],
        [InlineKeyboardButton("Premium Photography - 15,000 ETB", callback_data='ph_15k')],
        [InlineKeyboardButton("Videography - 15,000 ETB", callback_data='ph_15k_vid')],
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='ph_back')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await update.message.reply_text(
        "5. Select Package / ፓኬጅ ይምረጡ:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return PH_PACKAGE

async def ph_step5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photography package selection"""
    query = update.callback_query
    await query.answer()
    context.user_data['ph_package'] = query.data
    lang = context.user_data.get('lang', 'en')
    
    # Payment warning
    warning_msg = (
        "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
        "Booking will not be confirmed unless a screenshot of the half-payment is sent.\n"
        "ያስያዙት ቦታ የሚረጋገጠው የግማሽ ክፍያ ስክሪን ሾት ከተላከ በኋላ ብቻ ነው።\n\n"
        "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
        "🏧 *Commercial Bank of Ethiopia (CBE)*\n"
        "👤 Account Name: AGOS POSTPARTUM CARE\n"
        "🔢 Account Number: 10001345678901\n\n"
        "📱 *Tele Birr / ቴሌ ብር*\n"
        "📞 Phone: 0967621545"
    )
    
    await query.message.reply_text(warning_msg, parse_mode='Markdown')
    await query.message.reply_text(
        "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
        reply_markup=get_nav_kb(lang, back_callback='ph_back')
    )
    return PH_PAYMENT

async def ph_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photography payment screenshot"""
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo. / እባክዎ ፎቶ ይላኩ።",
            reply_markup=get_nav_kb(lang, back_callback='ph_back')
        )
        return PH_PAYMENT

    pay_img = update.message.photo[-1].file_id
    
    summary = (f"🔔 **NEW MEDIA BOOKING / አዲስ የሚዲያ ትዕዛዝ** 🔔\n\n"
               f"👤 Name / ስም: {context.user_data.get('ph_name')}\n"
               f"📞 Phone / ስልክ: {context.user_data.get('ph_phone')}\n"
               f"📅 Date / ቀን: {context.user_data.get('ph_date')}\n"
               f"🏠 Address / አድራሻ: {context.user_data.get('ph_addr')}\n"
               f"🎁 Package / ፓኬጅ: {context.user_data.get('ph_package')}")

    # Send to all admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=pay_img, caption=summary, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")

    await update.message.reply_text(
        "✅ Your booking is awaiting confirmation. / ማረጋገጫ በመጠበቅ ላይ።"
    )
    
    # Show discover more page
    await show_discover_more(update, context)
    
    return ConversationHandler.END

# --- APP RUNNER ---
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Decor booking conversation handler
    d_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(d_start, pattern='^d_start$')],
        states={
            D_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step1)],
            D_GENDER: [CallbackQueryHandler(d_step2)],
            D_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step3)],
            D_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step4)],
            D_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step5)],
            D_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step6)],
            D_PKG: [CallbackQueryHandler(d_step7)],
            D_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step8)],
            D_HOUSE: [CallbackQueryHandler(d_step9)],
            D_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step10)],
            D_PAYMENT: [MessageHandler(filters.PHOTO, d_final)]
        },
        fallbacks=[CommandHandler("start", start), 
                  CallbackQueryHandler(show_menu, pattern='^menu$'), 
                  CallbackQueryHandler(start, pattern='^restart$')],
        allow_reentry=True
    )

    # Limousine booking conversation handler
    l_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(l_start, pattern='^l_start$')],
        states={
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step1)],
            L_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step2)],
            L_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step3)],
            L_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step4)],
            L_PACKAGE: [CallbackQueryHandler(l_step5)],
            L_PAYMENT: [MessageHandler(filters.PHOTO, l_final)]
        },
        fallbacks=[CommandHandler("start", start), 
                  CallbackQueryHandler(show_menu, pattern='^menu$'), 
                  CallbackQueryHandler(start, pattern='^restart$')],
        allow_reentry=True
    )

    # Photography booking conversation handler
    ph_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ph_start, pattern='^ph_start$')],
        states={
            PH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step1)],
            PH_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step2)],
            PH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step3)],
            PH_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step4)],
            PH_PACKAGE: [CallbackQueryHandler(ph_step5)],
            PH_PAYMENT: [MessageHandler(filters.PHOTO, ph_final)]
        },
        fallbacks=[CommandHandler("start", start), 
                  CallbackQueryHandler(show_menu, pattern='^menu$'), 
                  CallbackQueryHandler(start, pattern='^restart$')],
        allow_reentry=True
    )

    # Add all handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(after_hours_handler, pattern='^after_hours$'))
    app.add_handler(CallbackQueryHandler(lambda u, c: show_menu(u, c, u.callback_query.data.split('_')[1]), pattern='^lang_'))
    app.add_handler(CallbackQueryHandler(lambda u, c: show_menu(u, c), pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(info_pages, pattern='^info_'))
    app.add_handler(CallbackQueryHandler(send_services_pdf, pattern='^send_pdf$'))
    app.add_handler(CallbackQueryHandler(start, pattern='^restart$'))
    
    app.add_handler(d_conv)
    app.add_handler(l_conv)
    app.add_handler(ph_conv)

    print("AGOS Decor Bot is live with updated features...")
    print(f"Working hours: {WORKING_HOURS_START}:00 - {WORKING_HOURS_END}:00 LT")
    app.run_polling()
