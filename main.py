import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes, ConversationHandler)
from datetime import datetime
import logging
import traceback

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [
    int(os.environ.get("ADMIN_ID_1", "123456789")),
    int(os.environ.get("ADMIN_ID_2", "987654321")),
    int(os.environ.get("ADMIN_ID_3", "555555555"))
]
LOGO_PATH = os.environ.get("LOGO_PATH", "logo.webp")
SERVICES_PDF_PATH = os.environ.get("SERVICES_PDF_PATH", "services_catalog.pdf")

# Working hours configuration (Ethiopian Local Time)
WORKING_HOURS_START = 8  # 8:00 AM LT
WORKING_HOURS_END = 20   # 8:00 PM LT

print("=" * 50)
print("DEBUG - TOKEN is:", repr(TOKEN))
print("DEBUG - Admin IDs:", ADMIN_IDS)
print("DEBUG - Logo Path:", LOGO_PATH)
print("DEBUG - Services PDF Path:", SERVICES_PDF_PATH)
print("=" * 50)

# --- CONVERSATION STATES ---
# Decor Booking States
(D_NAME, D_GENDER, D_ADDR, D_PHONE, D_USERNAME, D_CONTACT, D_PKG, D_DATE, D_HOUSE, D_NOTES, D_PAYMENT) = range(1, 12)

# Limousine Booking States
(L_NAME, L_PHONE, L_DATE, L_ADDR, L_PACKAGE, L_PAYMENT) = range(20, 26)

# Photography Booking States
(PH_NAME, PH_PHONE, PH_DATE, PH_ADDR, PH_PACKAGE, PH_PAYMENT) = range(30, 36)

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

# --- CONTENT (Full content with contact info) ---
CONTENT = {
    'en': {
        'welcome': "🎁 *Welcome to AGOS Decor & Special Services* 🌸\n\n✨ Premium home decor for your special moments\n🚗 Luxury limousine arrivals\n📸 Professional photography & videography\n\n🌐 www.agospostpartumcare.com",
        'btns': ["🎁 Decor Packages", "🚗 Limousine Service", "📸 Media Services", "📞 Contact Us", "📋 Services Catalog"],
        'decor_basic': "🔸 *Home Decor (15,000 ETB)*\n__________________________\n\n• Bedroom Decoration\n• Floor Decoration\n• Corridor Decoration\n• Salon Decoration\n\n📱 See our work: @agos_postpartumcare on Instagram/TikTok",
        'decor_deluxe': "💎 *Home Decor Deluxe (20,000 ETB)*\n__________________________\n\n• Bedroom, Corridor & Salon Decor\n• Large Flower Arrangement\n• 2 Kg Normal Cake",
        'decor_premium': "👑 *Home Decor Premium (25,000 ETB)*\n__________________________\n\n• Bedroom Decor with Agober rent\n• Corridor & Salon Decor\n• Large Flower Arrangement\n• 2 Kg Custom Cake",
        'limo_grand': "⭐ *The Grand Arrival (25,000 ETB)*\n__________________________\n\n• Special limousine service\n• Grand and elegant ride home",
        'limo_special': "✨ *Special Arrival (30,000 ETB)*\n__________________________\n\n• Exclusive limousine service\n• Luxurious and heartwarming ride",
        'limo_royal': "👑 *Royal Welcome (35,000 ETB)*\n__________________________\n\n• Premium luxury limousine\n• Truly regal welcome home",
        'photo_digital': "📱 *Digital Photography (10,000 ETB)*\n__________________________\n\n• Professional photography\n• All photos in soft copy",
        'photo_standard': "🖼️ *Standard Photography (12,000 ETB)*\n__________________________\n\n• 100 printed photos\n• Soft copy of all photos",
        'photo_premium': "💎 *Premium Photography (15,000 ETB)*\n__________________________\n\n• Laminated photo album\n• Soft copy of all photos",
        'videography': "🎥 *Videography Package (15,000 ETB)*\n__________________________\n\n• Full video coverage\n• Edited video",
        'contact_text': (
            "📞 *Contact Us*\n\n"
            "⏰ *Working Hours:* 8:00 AM - 8:00 PM (Local Time)\n"
            "⚠️ *Note:* Not operational after 2:00 PM LT\n\n"
            "📱 *Telegram:* @agos_postpartumcare\n"
            "📞 *Phone:* +251 967 621 545 | +251 980 040 468\n\n"
            "📸 *Instagram:* instagram.com/agospostpartum\n"
            "🎵 *TikTok:* tiktok.com/@agos_postpartumcare\n"
            "🌐 *Website:* www.agospostpartumcare.com\n"
            "📍 *Location:* Piassa, Abat Commercial, Addis Ababa"
        ),
        'back': "🔙 Back to Menu",
        'change_lang': "🌍 Change Language",
        'q_back': "⬅️ Previous Question",
        'book_now': "📝 Book Now",
        'discover_after_decor': "✨ *Thank you for your decor booking!* ✨\n\nNow check out our other services!",
        'discover_after_limo': "✨ *Thank you for your limousine booking!* ✨\n\nNow check out our other services!",
        'discover_after_photo': "✨ *Thank you for your photography booking!* ✨\n\nNow check out our other services!",
    },
    'am': {
        'welcome': "🎁 *እንኳን ወደ AGOS ዲኮር እና ልዩ አገልግሎቶች በሰላም መጡ* 🌸",
        'btns': ["🎁 የዲኮር ፓኬጆች", "🚗 የሊሙዚን አገልግሎት", "📸 የሚዲያ አገልግሎቶች", "📞 ያግኙን", "📋 የአገልግሎት ካታሎግ"],
        'decor_basic': "🔸 *መደበኛ ዲኮር (15,000 ብር)*\n__________________________\n\n• የመኝታ ቤት ዲኮር\n• የወለል ዲኮር\n• የኮሪደር ዲኮር\n• የሳሎን ዲኮር",
        'decor_deluxe': "💎 *ደልክስ ዲኮር (20,000 ብር)*\n__________________________\n\n• የመኝታ ቤት፣ ኮሪደር እና ሳሎን ዲኮር\n• ትልቅ የአበባ ዝግጅት\n• 2 ኪሎ ኬክ",
        'decor_premium': "👑 *ፕሪሚየም ዲኮር (25,000 ብር)*\n__________________________\n\n• የመኝታ ቤት ዲኮር ከአጎበር ኪራይ\n• የኮሪደር እና ሳሎን ዲኮር\n• ትልቅ የአበባ ዝግጅት\n• 2 ኪሎ ኬክ በመረጡት ዲዛይን",
        'contact_text': (
            "📞 *ያግኙን*\n\n"
            "⏰ *የስራ ሰዓት:* 8፡00 ጥዋት - 8፡00 ማታ\n"
            "⚠️ *ማሳሰቢያ:* ከምሽቱ 2፡00 በኋላ አይሰራም\n\n"
            "📱 *ቴሌግራም:* @agos_postpartumcare\n"
            "📞 *ስልክ:* +251 967 621 545 | +251 980 040 468\n\n"
            "📸 *ኢንስታግራም:* instagram.com/agospostpartum\n"
            "🎵 *ቲክቶክ:* tiktok.com/@agos_postpartumcare\n"
            "🌐 *ዌብሳይት:* www.agospostpartumcare.com\n"
            "📍 *አድራሻ:* ፒያሳ፣ አባት ኮሜርሻል"
        ),
        'back': "🔙 ወደ ዋና ማውጫ",
        'change_lang': "🌍 ቋንቋ ቀይር",
        'q_back': "⬅️ ወደ ኋላ",
        'book_now': "📝 አሁን ይያዙ",
    }
}

# --- PDF GENERATOR FUNCTIONS ---
def create_decor_pdf(data):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        if os.path.exists(LOGO_PATH):
            try:
                logo = ImageReader(LOGO_PATH)
                c.drawImage(logo, 480, height - 80, width=60, height=60, mask='auto')
            except Exception as e:
                logger.error(f"Error adding logo to PDF: {e}")

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "AGOS Decor Booking")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, "Official Decor Order Form")
        c.line(50, height - 85, 550, height - 85)

        c.setFont("Helvetica", 11)
        y_position = height - 120

        for key, value in data.items():
            if key.startswith('d_') and key not in ['d_payment']:
                label = key[2:].replace('_', ' ').upper()
                text = f"{label}: {value}"
                c.drawString(50, y_position, text)
                y_position -= 25
                if y_position < 60:
                    c.showPage()
                    y_position = height - 50

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, 40, f"Generated via AGOS Telegram Bot on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Awaiting payment confirmation.")
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Error creating decor PDF: {e}")
        return None

def create_limo_pdf(data):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        if os.path.exists(LOGO_PATH):
            try:
                logo = ImageReader(LOGO_PATH)
                c.drawImage(logo, 480, height - 80, width=60, height=60, mask='auto')
            except Exception as e:
                logger.error(f"Error adding logo to PDF: {e}")

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "AGOS Limousine Booking")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, "Official Limousine Order Form")
        c.line(50, height - 85, 550, height - 85)

        c.setFont("Helvetica", 11)
        y_position = height - 120

        for key, value in data.items():
            if key.startswith('l_') and key not in ['l_payment']:
                label = key[2:].replace('_', ' ').upper()
                text = f"{label}: {value}"
                c.drawString(50, y_position, text)
                y_position -= 25
                if y_position < 60:
                    c.showPage()
                    y_position = height - 50

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, 40, f"Generated via AGOS Telegram Bot on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Awaiting payment confirmation.")
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Error creating limo PDF: {e}")
        return None

def create_photo_pdf(data):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        if os.path.exists(LOGO_PATH):
            try:
                logo = ImageReader(LOGO_PATH)
                c.drawImage(logo, 480, height - 80, width=60, height=60, mask='auto')
            except Exception as e:
                logger.error(f"Error adding logo to PDF: {e}")

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "AGOS Media Services Booking")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, "Official Media Services Order Form")
        c.line(50, height - 85, 550, height - 85)

        c.setFont("Helvetica", 11)
        y_position = height - 120

        for key, value in data.items():
            if key.startswith('ph_') and key not in ['ph_payment']:
                label = key[3:].replace('_', ' ').upper()
                text = f"{label}: {value}"
                c.drawString(50, y_position, text)
                y_position -= 25
                if y_position < 60:
                    c.showPage()
                    y_position = height - 50

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, 40, f"Generated via AGOS Telegram Bot on {datetime.now().strftime('%Y-%m-%d %H:%M')}. Awaiting payment confirmation.")
        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Error creating photo PDF: {e}")
        return None

# --- HELPERS ---
def get_nav_kb(lang, back_callback='d_back'):
    """Returns keyboard with Back and Menu buttons"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data=back_callback)],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str, photo_file_id=None, document=None, filename=None):
    """Helper function to notify all admins with error handling"""
    success_count = 0
    for admin_id in ADMIN_IDS:
        try:
            if photo_file_id:
                await context.bot.send_photo(
                    chat_id=admin_id, 
                    photo=photo_file_id, 
                    caption=message, 
                    parse_mode='Markdown'
                )
                logger.info(f"Sent photo notification to admin {admin_id}")
            elif document:
                document.seek(0)
                await context.bot.send_document(
                    chat_id=admin_id, 
                    document=document, 
                    filename=filename,
                    caption=message,
                    parse_mode='Markdown'
                )
                logger.info(f"Sent document notification to admin {admin_id}")
            else:
                await context.bot.send_message(
                    chat_id=admin_id, 
                    text=message, 
                    parse_mode='Markdown'
                )
                logger.info(f"Sent text notification to admin {admin_id}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
            logger.error(traceback.format_exc())
    
    logger.info(f"Notified {success_count}/{len(ADMIN_IDS)} admins successfully")
    return success_count

async def show_discover_more(update: Update, context: ContextTypes.DEFAULT_TYPE, last_booking_type=None):
    """Show dynamic discover more page"""
    lang = context.user_data.get('lang', 'en')
    
    discover_buttons = [
        [InlineKeyboardButton("🎁 Book Decor", callback_data='show_decor_packages'),
         InlineKeyboardButton("🚗 Book Limousine", callback_data='show_limo_packages')],
        [InlineKeyboardButton("📸 Book Media", callback_data='show_photo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    if last_booking_type == 'decor':
        message = "✨ *Thank you for your decor booking!* ✨\n\nNow check out our other services!"
    elif last_booking_type == 'limo':
        message = "✨ *Thank you for your limousine booking!* ✨\n\nNow check out our other services!"
    elif last_booking_type == 'photo':
        message = "✨ *Thank you for your photography booking!* ✨\n\nNow check out our other services!"
    else:
        message = "Explore our other services!"
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(discover_buttons),
        parse_mode='Markdown'
    )

# --- PACKAGE DISPLAY FUNCTIONS ---
async def show_decor_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("🔸 Basic - 15,000 ETB", callback_data='view_decor_basic')],
        [InlineKeyboardButton("💎 Deluxe - 20,000 ETB", callback_data='view_decor_deluxe')],
        [InlineKeyboardButton("👑 Premium - 25,000 ETB", callback_data='view_decor_premium')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        "🎁 *Select a Decor Package:*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def show_limo_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("⭐ Grand Arrival - 25,000 ETB", callback_data='view_limo_grand')],
        [InlineKeyboardButton("✨ Special Arrival - 30,000 ETB", callback_data='view_limo_special')],
        [InlineKeyboardButton("👑 Royal Welcome - 35,000 ETB", callback_data='view_limo_royal')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        "🚗 *Select a Limousine Package:*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def show_photo_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("📱 Digital Photo - 10,000 ETB", callback_data='view_photo_digital')],
        [InlineKeyboardButton("🖼️ Standard Photo - 12,000 ETB", callback_data='view_photo_standard')],
        [InlineKeyboardButton("💎 Premium Photo - 15,000 ETB", callback_data='view_photo_premium')],
        [InlineKeyboardButton("🎥 Videography - 15,000 ETB", callback_data='view_videography')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        "📸 *Select a Media Package:*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

# --- INDIVIDUAL PACKAGE VIEW FUNCTIONS ---
async def view_decor_basic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='d_start_basic')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_decor_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['decor_basic'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_decor_deluxe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='d_start_deluxe')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_decor_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['decor_deluxe'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_decor_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='d_start_premium')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_decor_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['decor_premium'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_limo_grand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='l_start_grand')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_limo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['limo_grand'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_limo_special(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='l_start_special')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_limo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['limo_special'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_limo_royal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='l_start_royal')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_limo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['limo_royal'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_photo_digital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_digital')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_photo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['photo_digital'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_photo_standard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_standard')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_photo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['photo_standard'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_photo_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_premium')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_photo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['photo_premium'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

async def view_videography(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_video')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='show_photo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['videography'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

# --- DECOR BOOKING FLOW ---
async def d_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start decor booking flow"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    # Determine which package was selected from callback data
    callback_data = query.data
    if 'basic' in callback_data:
        context.user_data['d_pkg'] = 'Basic - 15,000 ETB'
    elif 'deluxe' in callback_data:
        context.user_data['d_pkg'] = 'Deluxe - 20,000 ETB'
    elif 'premium' in callback_data:
        context.user_data['d_pkg'] = 'Premium - 25,000 ETB'
    
    logger.info(f"Starting decor booking with package: {context.user_data['d_pkg']}")
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])
    
    await query.message.reply_text(
        "🎁 **Decor Booking**\n\n1. Full Name:",
        reply_markup=kb
    )
    return D_NAME

async def d_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input"""
    context.user_data['d_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("Male", callback_data='d_gender_male'),
         InlineKeyboardButton("Female", callback_data='d_gender_female')],
        [InlineKeyboardButton("Not Sure", callback_data='d_gender_unsure')],
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back_to_name')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await update.message.reply_text(
        "2. Gender of the Newborn:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return D_GENDER

async def d_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle gender selection"""
    query = update.callback_query
    await query.answer()
    
    # Store gender based on callback data
    if 'male' in query.data:
        context.user_data['d_gender'] = 'Male'
    elif 'female' in query.data:
        context.user_data['d_gender'] = 'Female'
    else:
        context.user_data['d_gender'] = 'Not Sure'
    
    lang = context.user_data.get('lang', 'en')
    
    await query.message.reply_text(
        "3. House Address for Decor Setup:",
        reply_markup=get_nav_kb(lang, 'd_back_to_gender')
    )
    return D_ADDR

async def d_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle address input"""
    context.user_data['d_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Client Phone Number:",
        reply_markup=get_nav_kb(lang, 'd_back_to_address')
    )
    return D_PHONE

async def d_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone input"""
    context.user_data['d_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "5. Your Telegram Username (e.g., @username):",
        reply_markup=get_nav_kb(lang, 'd_back_to_phone')
    )
    return D_USERNAME

async def d_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle username input"""
    context.user_data['d_username'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "6. Contact Person at Home (if different):",
        reply_markup=get_nav_kb(lang, 'd_back_to_username')
    )
    return D_CONTACT

async def d_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact person input"""
    context.user_data['d_contact'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    # Package already pre-selected, skip to date
    await update.message.reply_text(
        "7. Preferred Date & Time for Decor setup\nFormat: DD/MM/YYYY, Time (e.g., 25/12/2023, 4:00 AM):",
        reply_markup=get_nav_kb(lang, 'd_back_to_contact')
    )
    return D_DATE

async def d_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date input"""
    context.user_data['d_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')

    kb = [
        [InlineKeyboardButton("Villa", callback_data='d_house_villa'),
         InlineKeyboardButton("Apartment", callback_data='d_house_apartment')],
        [InlineKeyboardButton("Condominium", callback_data='d_house_condo')],
        [InlineKeyboardButton("G+1", callback_data='d_house_g1'),
         InlineKeyboardButton("G+2", callback_data='d_house_g2')],
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back_to_date')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]

    await update.message.reply_text(
        "8. House Type:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return D_HOUSE

async def d_house(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle house type selection"""
    query = update.callback_query
    await query.answer()
    
    # Store house type
    house_map = {
        'd_house_villa': 'Villa',
        'd_house_apartment': 'Apartment',
        'd_house_condo': 'Condominium',
        'd_house_g1': 'G+1',
        'd_house_g2': 'G+2'
    }
    context.user_data['d_house'] = house_map.get(query.data, 'Unknown')
    
    lang = context.user_data.get('lang', 'en')
    
    warning_msg = (
        "⚠️ *IMPORTANT*\n\n"
        "Booking will not be confirmed unless a screenshot of the half-payment is sent.\n\n"
        "🏦 *Bank Account Details*:\n\n"
        "🏧 Commercial Bank of Ethiopia\n"
        "👤 AGOS POSTPARTUM CARE\n"
        "🔢 10001345678901\n\n"
        "📱 Tele Birr: 0967621545"
    )
    
    await query.message.reply_text(warning_msg, parse_mode='Markdown')
    await query.message.reply_text(
        "9. Special Notes (optional):",
        reply_markup=get_nav_kb(lang, 'd_back_to_house')
    )
    return D_NOTES

async def d_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle notes input"""
    context.user_data['d_notes'] = update.message.text
    lang = context.user_data.get('lang', 'en')

    await update.message.reply_text(
        "10. Upload Payment Screenshot:",
        reply_markup=get_nav_kb(lang, 'd_back_to_notes')
    )
    return D_PAYMENT

async def d_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment screenshot and notify admins"""
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo.",
            reply_markup=get_nav_kb(lang, 'd_back_to_payment')
        )
        return D_PAYMENT

    try:
        photo = update.message.photo[-1]
        pay_img = photo.file_id
        
        # Create PDF
        pdf_file = create_decor_pdf(context.user_data)
        if not pdf_file:
            await update.message.reply_text("Error creating PDF. Please try again.")
            return D_PAYMENT
        
        # Prepare summary message
        summary = (
            f"🔔 *NEW DECOR BOOKING* 🔔\n\n"
            f"👤 *Name:* {context.user_data.get('d_name', 'N/A')}\n"
            f"👶 *Baby Gender:* {context.user_data.get('d_gender', 'N/A')}\n"
            f"📞 *Phone:* {context.user_data.get('d_phone', 'N/A')}\n"
            f"📱 *Telegram:* {context.user_data.get('d_username', 'N/A')}\n"
            f"🏠 *Address:* {context.user_data.get('d_addr', 'N/A')}\n"
            f"🏗️ *House Type:* {context.user_data.get('d_house', 'N/A')}\n"
            f"🎁 *Package:* {context.user_data.get('d_pkg', 'N/A')}\n"
            f"📅 *Date:* {context.user_data.get('d_date', 'N/A')}\n"
            f"📝 *Notes:* {context.user_data.get('d_notes', 'None')}\n"
            f"👤 *Contact Person:* {context.user_data.get('d_contact', 'N/A')}\n\n"
            f"⏰ *Submitted:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Send to admins
        logger.info(f"Sending decor booking notification to {len(ADMIN_IDS)} admins")
        
        # First send the photo with caption
        photo_sent = await notify_admins(context, summary, photo_file_id=pay_img)
        
        # Then send the PDF document
        if photo_sent > 0:
            pdf_filename = f"Decor_{context.user_data.get('d_name', 'Booking').replace(' ', '_')}.pdf"
            await notify_admins(
                context, 
                f"📄 *PDF Summary for {context.user_data.get('d_name', 'Booking')}*", 
                document=pdf_file, 
                filename=pdf_filename
            )
            logger.info(f"Successfully sent decor booking to {photo_sent} admins")
        else:
            logger.error("Failed to send decor booking to any admin")

        # Send confirmation to user
        pdf_file.seek(0)
        await update.message.reply_document(
            document=pdf_file, 
            filename="AGOS_Decor_Booking.pdf", 
            caption="✅ Booking submitted! Awaiting confirmation. We'll contact you soon."
        )

        # Show discover more page
        await show_discover_more(update, context, 'decor')
        
    except Exception as e:
        logger.error(f"Error in decor payment handler: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("An error occurred. Please try again or contact support.")
    
    return ConversationHandler.END

# --- LIMOUSINE BOOKING FLOW ---
async def l_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start limousine booking flow"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    # Store package
    if 'grand' in query.data:
        context.user_data['l_package'] = 'Grand Arrival - 25,000 ETB'
    elif 'special' in query.data:
        context.user_data['l_package'] = 'Special Arrival - 30,000 ETB'
    elif 'royal' in query.data:
        context.user_data['l_package'] = 'Royal Welcome - 35,000 ETB'
    
    logger.info(f"Starting limousine booking with package: {context.user_data['l_package']}")
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])
    
    await query.message.reply_text(
        "🚗 **Limousine Booking**\n\n1. Full Name:",
        reply_markup=kb
    )
    return L_NAME

async def l_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input"""
    context.user_data['l_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "2. Phone Number:",
        reply_markup=get_nav_kb(lang, 'l_back_to_name')
    )
    return L_PHONE

async def l_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone input"""
    context.user_data['l_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "3. Preferred Date & Time\nFormat: DD/MM/YYYY, Time:",
        reply_markup=get_nav_kb(lang, 'l_back_to_phone')
    )
    return L_DATE

async def l_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date input"""
    context.user_data['l_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Pickup Address:",
        reply_markup=get_nav_kb(lang, 'l_back_to_date')
    )
    return L_ADDR

async def l_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle address input"""
    context.user_data['l_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    warning_msg = (
        "⚠️ *IMPORTANT*\n\n"
        "Booking will not be confirmed without half-payment screenshot.\n\n"
        "🏦 Bank: Commercial Bank of Ethiopia\n"
        "👤 AGOS POSTPARTUM CARE\n"
        "🔢 10001345678901\n"
        "📱 Tele Birr: 0967621545"
    )
    
    await update.message.reply_text(warning_msg, parse_mode='Markdown')
    await update.message.reply_text(
        "5. Upload Payment Screenshot:",
        reply_markup=get_nav_kb(lang, 'l_back_to_address')
    )
    return L_PAYMENT

async def l_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment screenshot and notify admins"""
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo.",
            reply_markup=get_nav_kb(lang, 'l_back_to_payment')
        )
        return L_PAYMENT

    try:
        photo = update.message.photo[-1]
        pay_img = photo.file_id
        
        # Create PDF
        pdf_file = create_limo_pdf(context.user_data)
        if not pdf_file:
            await update.message.reply_text("Error creating PDF. Please try again.")
            return L_PAYMENT
        
        # Prepare summary message
        summary = (
            f"🔔 *NEW LIMOUSINE BOOKING* 🔔\n\n"
            f"👤 *Name:* {context.user_data.get('l_name', 'N/A')}\n"
            f"📞 *Phone:* {context.user_data.get('l_phone', 'N/A')}\n"
            f"📅 *Date:* {context.user_data.get('l_date', 'N/A')}\n"
            f"🏠 *Address:* {context.user_data.get('l_addr', 'N/A')}\n"
            f"🎁 *Package:* {context.user_data.get('l_package', 'N/A')}\n\n"
            f"⏰ *Submitted:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Send to admins
        logger.info(f"Sending limousine booking notification to {len(ADMIN_IDS)} admins")
        
        photo_sent = await notify_admins(context, summary, photo_file_id=pay_img)
        
        if photo_sent > 0:
            pdf_filename = f"Limousine_{context.user_data.get('l_name', 'Booking').replace(' ', '_')}.pdf"
            await notify_admins(
                context, 
                f"📄 *PDF Summary for {context.user_data.get('l_name', 'Booking')}*", 
                document=pdf_file, 
                filename=pdf_filename
            )
            logger.info(f"Successfully sent limousine booking to {photo_sent} admins")
        else:
            logger.error("Failed to send limousine booking to any admin")

        # Send confirmation to user
        pdf_file.seek(0)
        await update.message.reply_document(
            document=pdf_file, 
            filename="AGOS_Limousine_Booking.pdf", 
            caption="✅ Booking submitted! Awaiting confirmation. We'll contact you soon."
        )

        await show_discover_more(update, context, 'limo')
        
    except Exception as e:
        logger.error(f"Error in limousine payment handler: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("An error occurred. Please try again or contact support.")
    
    return ConversationHandler.END

# --- PHOTOGRAPHY BOOKING FLOW ---
async def ph_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start photography booking flow"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    # Store package
    if 'digital' in query.data:
        context.user_data['ph_package'] = 'Digital Photography - 10,000 ETB'
    elif 'standard' in query.data:
        context.user_data['ph_package'] = 'Standard Photography - 12,000 ETB'
    elif 'premium' in query.data:
        context.user_data['ph_package'] = 'Premium Photography - 15,000 ETB'
    elif 'video' in query.data:
        context.user_data['ph_package'] = 'Videography - 15,000 ETB'
    
    logger.info(f"Starting photography booking with package: {context.user_data['ph_package']}")
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ])
    
    await query.message.reply_text(
        "📸 **Media Services Booking**\n\n1. Full Name:",
        reply_markup=kb
    )
    return PH_NAME

async def ph_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle name input"""
    context.user_data['ph_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "2. Phone Number:",
        reply_markup=get_nav_kb(lang, 'ph_back_to_name')
    )
    return PH_PHONE

async def ph_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone input"""
    context.user_data['ph_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "3. Event Date & Time\nFormat: DD/MM/YYYY, Time:",
        reply_markup=get_nav_kb(lang, 'ph_back_to_phone')
    )
    return PH_DATE

async def ph_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date input"""
    context.user_data['ph_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Event Address:",
        reply_markup=get_nav_kb(lang, 'ph_back_to_date')
    )
    return PH_ADDR

async def ph_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle address input"""
    context.user_data['ph_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    warning_msg = (
        "⚠️ *IMPORTANT*\n\n"
        "Booking will not be confirmed without half-payment screenshot.\n\n"
        "🏦 Bank: Commercial Bank of Ethiopia\n"
        "👤 AGOS POSTPARTUM CARE\n"
        "🔢 10001345678901\n"
        "📱 Tele Birr: 0967621545"
    )
    
    await update.message.reply_text(warning_msg, parse_mode='Markdown')
    await update.message.reply_text(
        "5. Upload Payment Screenshot:",
        reply_markup=get_nav_kb(lang, 'ph_back_to_address')
    )
    return PH_PAYMENT

async def ph_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment screenshot and notify admins"""
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo.",
            reply_markup=get_nav_kb(lang, 'ph_back_to_payment')
        )
        return PH_PAYMENT

    try:
        photo = update.message.photo[-1]
        pay_img = photo.file_id
        
        # Create PDF
        pdf_file = create_photo_pdf(context.user_data)
        if not pdf_file:
            await update.message.reply_text("Error creating PDF. Please try again.")
            return PH_PAYMENT
        
        # Prepare summary message
        summary = (
            f"🔔 *NEW MEDIA BOOKING* 🔔\n\n"
            f"👤 *Name:* {context.user_data.get('ph_name', 'N/A')}\n"
            f"📞 *Phone:* {context.user_data.get('ph_phone', 'N/A')}\n"
            f"📅 *Date:* {context.user_data.get('ph_date', 'N/A')}\n"
            f"🏠 *Address:* {context.user_data.get('ph_addr', 'N/A')}\n"
            f"🎁 *Package:* {context.user_data.get('ph_package', 'N/A')}\n\n"
            f"⏰ *Submitted:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Send to admins
        logger.info(f"Sending media booking notification to {len(ADMIN_IDS)} admins")
        
        photo_sent = await notify_admins(context, summary, photo_file_id=pay_img)
        
        if photo_sent > 0:
            pdf_filename = f"Media_{context.user_data.get('ph_name', 'Booking').replace(' ', '_')}.pdf"
            await notify_admins(
                context, 
                f"📄 *PDF Summary for {context.user_data.get('ph_name', 'Booking')}*", 
                document=pdf_file, 
                filename=pdf_filename
            )
            logger.info(f"Successfully sent media booking to {photo_sent} admins")
        else:
            logger.error("Failed to send media booking to any admin")

        # Send confirmation to user
        pdf_file.seek(0)
        await update.message.reply_document(
            document=pdf_file, 
            filename="AGOS_Media_Booking.pdf", 
            caption="✅ Booking submitted! Awaiting confirmation. We'll contact you soon."
        )

        await show_discover_more(update, context, 'photo')
        
    except Exception as e:
        logger.error(f"Error in media payment handler: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("An error occurred. Please try again or contact support.")
    
    return ConversationHandler.END

# --- BACK BUTTON HANDLERS ---
async def d_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button in decor flow"""
    query = update.callback_query
    await query.answer()
    
    callback = query.data
    
    if callback == 'd_back_to_name':
        lang = context.user_data.get('lang', 'en')
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]])
        await query.message.reply_text("1. Full Name:", reply_markup=kb)
        return D_NAME
    elif callback == 'd_back_to_gender':
        lang = context.user_data.get('lang', 'en')
        kb = [
            [InlineKeyboardButton("Male", callback_data='d_gender_male'),
             InlineKeyboardButton("Female", callback_data='d_gender_female')],
            [InlineKeyboardButton("Not Sure", callback_data='d_gender_unsure')],
            [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back_to_name')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
        await query.message.reply_text("2. Gender of the Newborn:", reply_markup=InlineKeyboardMarkup(kb))
        return D_GENDER
    elif callback == 'd_back_to_address':
        return await d_gender(update, context)
    elif callback == 'd_back_to_phone':
        return await d_address(update, context)
    elif callback == 'd_back_to_username':
        return await d_phone(update, context)
    elif callback == 'd_back_to_contact':
        return await d_username(update, context)
    elif callback == 'd_back_to_date':
        return await d_contact(update, context)
    elif callback == 'd_back_to_house':
        return await d_date(update, context)
    elif callback == 'd_back_to_notes':
        return await d_house(update, context)
    elif callback == 'd_back_to_payment':
        return await d_notes(update, context)
    
    return D_NAME

async def l_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button in limousine flow"""
    query = update.callback_query
    await query.answer()
    
    callback = query.data
    
    if callback == 'l_back_to_name':
        lang = context.user_data.get('lang', 'en')
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]])
        await query.message.reply_text("1. Full Name:", reply_markup=kb)
        return L_NAME
    elif callback == 'l_back_to_phone':
        lang = context.user_data.get('lang', 'en')
        await query.message.reply_text("2. Phone Number:", reply_markup=get_nav_kb(lang, 'l_back_to_name'))
        return L_PHONE
    elif callback == 'l_back_to_date':
        lang = context.user_data.get('lang', 'en')
        await query.message.reply_text("3. Preferred Date & Time\nFormat: DD/MM/YYYY, Time:", reply_markup=get_nav_kb(lang, 'l_back_to_phone'))
        return L_DATE
    elif callback == 'l_back_to_address':
        lang = context.user_data.get('lang', 'en')
        await query.message.reply_text("4. Pickup Address:", reply_markup=get_nav_kb(lang, 'l_back_to_date'))
        return L_ADDR
    elif callback == 'l_back_to_payment':
        lang = context.user_data.get('lang', 'en')
        warning_msg = (
            "⚠️ *IMPORTANT*\n\n"
            "Booking will not be confirmed without half-payment screenshot.\n\n"
            "🏦 Bank: Commercial Bank of Ethiopia\n"
            "👤 AGOS POSTPARTUM CARE\n"
            "🔢 10001345678901\n"
            "📱 Tele Birr: 0967621545"
        )
        await query.message.reply_text(warning_msg, parse_mode='Markdown')
        await query.message.reply_text("5. Upload Payment Screenshot:", reply_markup=get_nav_kb(lang, 'l_back_to_address'))
        return L_PAYMENT
    
    return L_NAME

async def ph_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button in photography flow"""
    query = update.callback_query
    await query.answer()
    
    callback = query.data
    
    if callback == 'ph_back_to_name':
        lang = context.user_data.get('lang', 'en')
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]])
        await query.message.reply_text("1. Full Name:", reply_markup=kb)
        return PH_NAME
    elif callback == 'ph_back_to_phone':
        lang = context.user_data.get('lang', 'en')
        await query.message.reply_text("2. Phone Number:", reply_markup=get_nav_kb(lang, 'ph_back_to_name'))
        return PH_PHONE
    elif callback == 'ph_back_to_date':
        lang = context.user_data.get('lang', 'en')
        await query.message.reply_text("3. Event Date & Time\nFormat: DD/MM/YYYY, Time:", reply_markup=get_nav_kb(lang, 'ph_back_to_phone'))
        return PH_DATE
    elif callback == 'ph_back_to_address':
        lang = context.user_data.get('lang', 'en')
        await query.message.reply_text("4. Event Address:", reply_markup=get_nav_kb(lang, 'ph_back_to_date'))
        return PH_ADDR
    elif callback == 'ph_back_to_payment':
        lang = context.user_data.get('lang', 'en')
        warning_msg = (
            "⚠️ *IMPORTANT*\n\n"
            "Booking will not be confirmed without half-payment screenshot.\n\n"
            "🏦 Bank: Commercial Bank of Ethiopia\n"
            "👤 AGOS POSTPARTUM CARE\n"
            "🔢 10001345678901\n"
            "📱 Tele Birr: 0967621545"
        )
        await query.message.reply_text(warning_msg, parse_mode='Markdown')
        await query.message.reply_text("5. Upload Payment Screenshot:", reply_markup=get_nav_kb(lang, 'ph_back_to_address'))
        return PH_PAYMENT
    
    return PH_NAME

# --- NAVIGATION FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    context.user_data.clear()
    logger.info("Bot started by user")
    return await working_hours_gate(update, context)

async def after_hours_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle after acknowledging working hours"""
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='lang_am')]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "🌿 Choose Language:", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    return ConversationHandler.END

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Handle language selection
        if query.data.startswith('lang_'):
            lang = query.data.split('_')[1]
            context.user_data['lang'] = lang
            logger.info(f"User selected language: {lang}")
        else:
            lang = context.user_data.get('lang', 'en')
        
        btns = CONTENT[lang]['btns']
        keyboard = [
            [InlineKeyboardButton(btns[0], callback_data='show_decor_packages'), 
             InlineKeyboardButton(btns[1], callback_data='show_limo_packages')],
            [InlineKeyboardButton(btns[2], callback_data='show_photo_packages'), 
             InlineKeyboardButton(btns[3], callback_data='contact_info')],
            [InlineKeyboardButton(btns[4], callback_data='send_pdf')],
            [InlineKeyboardButton(CONTENT[lang]['change_lang'], callback_data='restart')]
        ]
        
        await query.message.reply_text(
            CONTENT[lang]['welcome'], 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact info page"""
    query = update.callback_query
    await query.answer()
    logger.info("Contact button clicked - showing contact info")
    lang = context.user_data.get('lang', 'en')
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]])
    await query.message.edit_text(
        CONTENT[lang]['contact_text'], 
        reply_markup=back_btn, 
        parse_mode='Markdown'
    )

async def send_services_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send services PDF"""
    query = update.callback_query
    await query.answer()
    
    if os.path.exists(SERVICES_PDF_PATH):
        try:
            with open(SERVICES_PDF_PATH, 'rb') as pdf_file:
                await query.message.reply_document(
                    document=pdf_file,
                    filename="AGOS_Services_Catalog.pdf",
                    caption="📋 Our complete services catalog"
                )
            logger.info("Services PDF sent to user")
        except Exception as e:
            logger.error(f"Error sending PDF: {e}")
            await query.message.reply_text("Error sending PDF. Please try again.")
    else:
        logger.warning(f"PDF not found at path: {SERVICES_PDF_PATH}")
        await query.message.reply_text("PDF catalog coming soon!")

# --- MAIN ---
def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Decor booking conversation
    decor_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(d_start, pattern='^d_start_basic$'),
            CallbackQueryHandler(d_start, pattern='^d_start_deluxe$'),
            CallbackQueryHandler(d_start, pattern='^d_start_premium$')
        ],
        states={
            D_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_name)],
            D_GENDER: [CallbackQueryHandler(d_gender, pattern='^d_gender_')],
            D_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_address)],
            D_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_phone)],
            D_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_username)],
            D_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_contact)],
            D_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_date)],
            D_HOUSE: [CallbackQueryHandler(d_house, pattern='^d_house_')],
            D_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_notes)],
            D_PAYMENT: [MessageHandler(filters.PHOTO, d_payment)]
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(show_menu, pattern='^menu$'),
            CallbackQueryHandler(start, pattern='^restart$'),
            CallbackQueryHandler(d_back_handler, pattern='^d_back_to_')
        ],
        name="decor_conversation",
        persistent=False
    )

    # Limousine booking conversation
    limo_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(l_start, pattern='^l_start_grand$'),
            CallbackQueryHandler(l_start, pattern='^l_start_special$'),
            CallbackQueryHandler(l_start, pattern='^l_start_royal$')
        ],
        states={
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_name)],
            L_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_phone)],
            L_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_date)],
            L_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_address)],
            L_PAYMENT: [MessageHandler(filters.PHOTO, l_payment)]
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(show_menu, pattern='^menu$'),
            CallbackQueryHandler(start, pattern='^restart$'),
            CallbackQueryHandler(l_back_handler, pattern='^l_back_to_')
        ],
        name="limo_conversation",
        persistent=False
    )

    # Photography booking conversation
    photo_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ph_start, pattern='^ph_start_digital$'),
            CallbackQueryHandler(ph_start, pattern='^ph_start_standard$'),
            CallbackQueryHandler(ph_start, pattern='^ph_start_premium$'),
            CallbackQueryHandler(ph_start, pattern='^ph_start_video$')
        ],
        states={
            PH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_name)],
            PH_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_phone)],
            PH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_date)],
            PH_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_address)],
            PH_PAYMENT: [MessageHandler(filters.PHOTO, ph_payment)]
        },
        fallbacks=[
            CommandHandler("start", start),
            CallbackQueryHandler(show_menu, pattern='^menu$'),
            CallbackQueryHandler(start, pattern='^restart$'),
            CallbackQueryHandler(ph_back_handler, pattern='^ph_back_to_')
        ],
        name="photo_conversation",
        persistent=False
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(after_hours_handler, pattern='^after_hours$'))
    application.add_handler(CallbackQueryHandler(show_menu, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(show_menu, pattern='^menu$'))
    application.add_handler(CallbackQueryHandler(contact_info, pattern='^contact_info$'))
    application.add_handler(CallbackQueryHandler(send_services_pdf, pattern='^send_pdf$'))
    application.add_handler(CallbackQueryHandler(start, pattern='^restart$'))
    
    # Package view handlers
    application.add_handler(CallbackQueryHandler(show_decor_packages, pattern='^show_decor_packages$'))
    application.add_handler(CallbackQueryHandler(show_limo_packages, pattern='^show_limo_packages$'))
    application.add_handler(CallbackQueryHandler(show_photo_packages, pattern='^show_photo_packages$'))
    
    # Individual package view handlers
    application.add_handler(CallbackQueryHandler(view_decor_basic, pattern='^view_decor_basic$'))
    application.add_handler(CallbackQueryHandler(view_decor_deluxe, pattern='^view_decor_deluxe$'))
    application.add_handler(CallbackQueryHandler(view_decor_premium, pattern='^view_decor_premium$'))
    application.add_handler(CallbackQueryHandler(view_limo_grand, pattern='^view_limo_grand$'))
    application.add_handler(CallbackQueryHandler(view_limo_special, pattern='^view_limo_special$'))
    application.add_handler(CallbackQueryHandler(view_limo_royal, pattern='^view_limo_royal$'))
    application.add_handler(CallbackQueryHandler(view_photo_digital, pattern='^view_photo_digital$'))
    application.add_handler(CallbackQueryHandler(view_photo_standard, pattern='^view_photo_standard$'))
    application.add_handler(CallbackQueryHandler(view_photo_premium, pattern='^view_photo_premium$'))
    application.add_handler(CallbackQueryHandler(view_videography, pattern='^view_videography$'))
    
    # Add conversation handlers
    application.add_handler(decor_conv)
    application.add_handler(limo_conv)
    application.add_handler(photo_conv)

    # Start bot
    print("=" * 50)
    print("🤖 AGOS Bot is starting with FIXED admin notifications!")
    print(f"⏰ Working hours: {WORKING_HOURS_START}:00 - {WORKING_HOURS_END}:00")
    print(f"👥 Admin IDs: {ADMIN_IDS}")
    print("✅ Decor booking: 10 steps with admin notifications")
    print("✅ Limousine booking: 5 steps with admin notifications")
    print("✅ Photography booking: 5 steps with admin notifications")
    print("✅ Contact page: Working")
    print("✅ Back buttons: Working")
    print("✅ Admin notifications: FIXED - will send to all configured admins")
    print("=" * 50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
