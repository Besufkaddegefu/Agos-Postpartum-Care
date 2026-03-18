import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes, ConversationHandler)
from datetime import datetime
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
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

print("DEBUG - TOKEN is:", repr(TOKEN))
print("DEBUG - Admin IDs:", ADMIN_IDS)

# --- CONVERSATION STATES ---
# Decor Booking States (must be unique numbers)
(D_NAME, D_GENDER, D_ADDR, D_PHONE, D_USERNAME, D_CONTACT, D_PKG, D_DATE, D_HOUSE, D_NOTES, D_PAYMENT) = range(40, 51)

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

# --- CONTENT (Your exact content preserved) ---
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
        'btns': ["🎁 Decor Packages", "🚗 Limousine Service", "📸 Photography Services", "📞 Contact Us", "📋 Services Catalog"],
        
        # Individual Decor Package Pages with Book Buttons
        'decor_basic': (
            "🔸 *Home Decor (15,000 ETB)*\n"
            "__________________________\n\n"
            "• Bedroom Decoration\n"
            "• Floor Decoration\n"
            "• Corridor Decoration\n"
            "• Salon Decoration\n\n"
            "📱 *👇👇👇See the previous projects we have done for 15,000 birr 👇👇👇:*\n"
            "[video](https://vm.tiktok.com/ZMA2PAHdX) | "
            "[video](https://vt.tiktok.com/ZSmoGPTJ6) | "
            "[video](https://vm.tiktok.com/ZMA2PV8vt) | "
            "[video](https://vt.tiktok.com/ZSmoGPTJ6) | "
            "✨ *Perfect for intimate celebrations!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'decor_deluxe': (
            "💎 *Home Decor Deluxe (20,000 ETB)*\n"
            "__________________________\n\n"
            "• Bedroom, Corridor & Salon Decor\n"
            "• Large Flower Arrangement (Bouquet + Floor) - እቅፍ አበባ\n"
            "• 2 Kg Normal Cake\n\n"
            "📱 *👇👇👇See the previous projects we have done for 20,000 birr 👇👇👇:*\n"
            "[video](https://vm.tiktok.com/ZMA2PQp4k) | "
            "[video](https://vm.tiktok.com/ZMA2PPv9g) | "
            "[video](https://vm.tiktok.com/ZMA2PbLWU) | "
            "[video](https://vm.tiktok.com/ZMA2PfLwK) | "
            "[video](https://vm.tiktok.com/ZMA2PG9Nd) | "
            "🌟 *Our most popular choice!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'decor_premium': (
            "👑 *Home Decor Premium (25,000 ETB)*\n"
            "__________________________\n\n"
            "• Bedroom Decor with Agober rent (2 weeks)\n"
            "• Corridor & Salon Decor\n"
            "• Large Flower Arrangement (Bouquet + Floor) - እቅፍ አበባ\n"
            "• 2 Kg Custom Made Cake - 2 ኪሎ ኬክ በመረጡት ዲዛይን\n\n"
            "📱 *👇👇👇See the previous projects we have done for 25,000 birr 👇👇👇:*\n"
            "[video](https://vm.tiktok.com/ZMA2Pb9Pp) | "
            "[video](https://vm.tiktok.com/ZMA2Pq1V8) | "
            "[video](https://vm.tiktok.com/ZMA2Pyn8m) | "
            "[video](https://vm.tiktok.com/ZMA2PqRTh) | "
            "[video](https://vm.tiktok.com/ZMA2PPpoG) | "
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7551840674677591352?_r=1&_t=ZM-914EEFmhm03) | "
            "👑 *The ultimate luxury experience!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        
        # Limousine Package Pages with Book Buttons
        'limo_grand': (
            "⭐ *The Grand Arrival (25,000 ETB)*\n"
            "__________________________\n\n"
            "• Special limousine service\n"
            "• Grand and elegant ride home\n"
            "• Professional chauffeur\n"
            "📸 *See our arrivals:*\n"
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7566665605512809740) | "
            "[Instagram](https://instagram.com/agospostpartum)\n\n"
            "🚗 *Make a stylish entrance!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'limo_special': (
            "✨ *Special Arrival (30,000 ETB)*\n"
            "__________________________\n\n"
            "• Exclusive limousine service\n"
            "• Luxurious and heartwarming ride\n"
            "• Professional chauffeur\n"
            "📸 *See our arrivals:*\n"
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7566665605512809740) | "
            "[Instagram](https://instagram.com/agospostpartum)\n\n"
            "✨ *Extra touches for a special day!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'limo_royal': (
            "👑 *Royal Welcome (35,000 ETB)*\n"
            "__________________________\n\n"
            "• Premium luxury limousine\n"
            "• Truly regal welcome home\n"
            "• Professional chauffeur in formal attire\n"
            "📸 *See our arrivals:*\n"
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7566665605512809740) | "
            "[Instagram](https://instagram.com/agospostpartum)\n\n"
            "👑 *Royal treatment for royalty!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        
        # Photography Package Pages with Book Buttons
        'photo_digital': (
            "📱 *Digital Photography (10,000 ETB)*\n"
            "__________________________\n\n"
            "• Professional photography\n"
            "• All photos delivered in soft copy\n"
            "• 2 hours coverage\n"
            "• (No physical album)\n\n"
            "📸 *See our portfolio:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "📱 *Perfect for digital sharing!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'photo_standard': (
            "🖼️ *Standard Photography (12,000 ETB)*\n"
            "__________________________\n\n"
            "• Normal album sized photos (100 printed)\n"
            "• Soft copy of all photos\n"
            "• 3 hours coverage\n\n"
            "📸 *See our portfolio:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "🖼️ *Beautiful memories you can hold!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'photo_premium': (
            "💎 *Premium Photography (15,000 ETB)*\n"
            "__________________________\n\n"
            "• Laminated photo album (20x30 cm)\n"
            "• Soft copy of all photos\n"
            "• 4 hours coverage\n"
            "• Professional editing\n\n"
            "📸 *See our portfolio:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "💎 *Heirloom quality memories!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'videography': (
            "🎥 *Videography Package (15,000 ETB)*\n"
            "__________________________\n\n"
            "• Full video coverage\n"
            "• Edited video (soft copy)\n"
            "• 4 hours coverage\n"
            "• Highlight reel\n\n"
            "📸 *See our portfolio:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "🎥 *Relive your special moments!*\n\n"
            "👉 *For more videos, visit our TikTok page at: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        
        'contact_text': (
            "📞 ••Contact Us••\n\n"
            "⏰ •Working Hours:• 8:00 AM - 8:00 PM (Local Time)\n"
            "⚠️ •Note:• Not operational before 2:00 LT / 8:00 PM\n\n"
            "📞 ••Phone:•• \n\n"
            "📱 +251 967 621 545\n"
            "📱 +251 980 040 468\n\n"
            "🎵 ••Follow us on :••\n"
            "📸 •Instagram: (https://instagram.com/agos_postpartumcare)\n"
            "🎵 •TikTok: (https://www.tiktok.com/@Agos_postpartumCare)\n"
            "📱 •Telegram: (https://t.me/Agospostpartumcare0)\n"
            "🌐 •Website: [www.agospostpartumcare.com]\n"
            "📍 •Location: [Piassa, Abat Commercial](https://maps.app.goo.gl/mHDvo7CpFwUubWyx6)"
        ),
        'agree_btn': "I Agree ✅",
        'back': "🔙 Back to Menu",
        'change_lang': "🌍 Change Language / ቋንቋ ቀይር",
        'q_back': "⬅️ Previous Question",
        
        # Dynamic Discover More messages
        'discover_after_decor': (
            "✨ Select if you want additional services until your decor order is confirmed.✨\n\n"
            "🚗 •Limousine Service - Make a grand entrance\n"
            "📸 •Photography Packages - Capture every moment\n\n"
            "Click below to explore more!"
        ),
        'discover_after_limo': (
            "✨ Select if you want additional services until your limousine order is confirmed.✨\n\n"
            "🎁 •Decor Packages - Create a beautiful space\n"
            "📸 •Photography Packages - Capture the moment\n\n"
            "Click below to explore more!"
        ),
        'discover_after_photo': (
            "✨ Select if you want additional services until your photography order is confirmed. ✨\n\n"
            "🎁 •Decor Packages - Create a beautiful space\n"
            "🚗 •Limousine Service - Make a grand entrance\n\n"
            "Click below to explore more!"
        ),
        'discover_complete': (
            "🎉 *You've explored all our services!* 🎉\n\n"
            "Thank you for choosing AGOS for your celebrations. You've booked:\n"
            "{booked_services}\n\n"
            "Want to add more? Contact us for custom packages!\n\n"
            "📞 •Contact: @agos_postpartumcare\n"
            "📱 •Phone: +251 967 621 545"
            "📱 •Phone: +251 980 040 468"
        ),
        'book_now': "📝 Book Now"
    },
    'am': {
        'welcome': (
            "🎁 *እንኳን ወደ AGOS ዲኮር እና ልዩ አገልግሎቶች በሰላም መጡ* 🌸\n\n"
            "✨ ለልዩ ጊዜያቶችዎ የሚሆን ፕሪሚየም የቤት ዲኮር\n"
            "🚗 የሊሙዚን አገልግሎት\n"
            "📸 ፕሮፌሽናል ፎቶግራፍ እና ቪዲዮግራፊ\n\n"
            "🌐 www.agospostpartumcare.com"
        ),
        'btns': ["🎁 የዲኮር ፓኬጆች", "🚗 የሊሙዚን አገልግሎት", "📸 የፎቶግራፍ አገልግሎቶች", "📞 ያግኙን", "📋 የአገልግሎት ዝርዝር"],
        
        # Individual Decor Package Pages with Book Buttons (Amharic)
        'decor_basic': (
            "🔸 *መደበኛ ዲኮር (15,000 ብር)*\n"
            "__________________________\n\n"
            "• የመኝታ ቤት ዲኮር\n"
            "• የወለል ዲኮር\n"
            "• የኮሪደር ዲኮር\n"
            "• የሳሎን ዲኮር\n\n"
            "📱 *👇👇👇ከዚህ በፊት በ 15,000 ብር የሰራናቸዉን ስራዎች ይመልከቱ 👇👇👇:*\n"
            "[video](https://vm.tiktok.com/ZMA2PAHdX) | "
            "[video](https://vt.tiktok.com/ZSmoGPTJ6) | "
            "[video](https://vm.tiktok.com/ZMA2PV8vt) | "
            "[video](https://vt.tiktok.com/ZSmoGPTJ6)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ*: https://www.tiktok.com/@agos_postpartumcare"
        ),
        'decor_deluxe': (
            "💎 *ደልክስ ዲኮር (20,000 ብር)*\n"
            "__________________________\n\n"
            "• የመኝታ ቤት፣ ኮሪደር እና ሳሎን ዲኮር\n"
            "• ትልቅ እቅፍ አበባ\n"
            "• 2 ኪሎ መደበኛ ኬክ\n\n"
            "📱 *👇👇👇ከዚህ በፊት በ 20,000 ብር የሰራናቸዉን ስራዎች ይመልከቱ 👇👇👇:*\n"
            "[video](https://vm.tiktok.com/ZMA2PQp4k) | "
            "[video](https://vm.tiktok.com/ZMA2PPv9g) | "
            "[video](https://vm.tiktok.com/ZMA2PbLWU) | "
            "[video](https://vm.tiktok.com/ZMA2PfLwK) | "
            "[video](https://vm.tiktok.com/ZMA2PG9Nd)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ*: https://www.tiktok.com/@agos_postpartumcare"
        ),
        'decor_premium': (
            "👑 *ፕሪሚየም ዲኮር (25,000 ብር)*\n"
            "__________________________\n\n"
            "• የመኝታ ቤት ዲኮር ከአጎበር ኪራይ ጋር (2 ሳምንት)\n"
            "• የኮሪደር እና ሳሎን ዲኮር\n"
            "• ትልቅ እቅፍ አበባ\n"
            "• 2 ኪሎ ኬክ በመረጡት ዲዛይን\n\n"
            "📱 *👇👇👇ከዚህ በፊት በ 25,000 ብር የሰራናቸዉን ስራዎች ይመልከቱ 👇👇👇:*\n"
            "[video](https://vm.tiktok.com/ZMA2Pb9Pp) | "
            "[video](https://vm.tiktok.com/ZMA2Pq1V8) | "
            "[video](https://vm.tiktok.com/ZMA2Pyn8m) | "
            "[video](https://vm.tiktok.com/ZMA2PqRTh) | "
            "[video](https://vm.tiktok.com/ZMA2PPpoG) | "
            "[video](https://surl.li/iiicng) | "
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7551840674677591352?_r=1&_t=ZM-914EEFmhm03) | "
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ*: https://www.tiktok.com/@agos_postpartumcare"
        ),
        
        # Limousine Package Pages with Book Buttons (Amharic)
        'limo_grand': (
            "⭐ *መደበኛ አቀባበል (25,000 ብር)*\n"
            "__________________________\n\n"
            "• ልዩ የሊሙዚን አገልግሎት\n\n"
            "📸 *አቀባበሎቻችንን ይመልከቱ:*\n"
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7566665605512809740) | "
            "[Instagram](https://instagram.com/agospostpartum)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ፦: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'limo_special': (
            "✨ *ልዩ አቀባበል (30,000 ብር)*\n"
            "__________________________\n\n"
            "• ልዩ የሊሙዚን አገልግሎት\n\n"
            "📸 *አቀባበሎቻችንን ይመልከቱ:*\n"
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7566665605512809740) | "
            "[Instagram](https://instagram.com/agospostpartum)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ፦: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'limo_royal': (
            "👑 *የሮያል አቀባበል (35,000 ብር)*\n"
            "__________________________\n\n"
            "• ፕሪሚየም የሊሙዚን አገልግሎት\n\n"
            "📸 *አቀበሎቻችንን ይመልከቱ:*\n"
            "[video](https://www.tiktok.com/@agos_postpartumcare/video/7566665605512809740e) | "
            "[Instagram](https://instagram.com/agospostpartum)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ፦: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        
        # Photography Package Pages with Book Buttons (Amharic)
        'photo_digital': (
            "📱 *ዲጂታል ፎቶግራፍ (10,000 ብር)*\n"
            "__________________________\n\n"
            "• የባለሙያ ፎቶግራፍ አገልግሎት\n"
            "• ሁሉም ፎቶዎች በሶፍት ኮፒ\n\n"
            "📸 *ስራዎቻችንን ይመልከቱ:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ፦: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'photo_standard': (
            "🖼️ *መደበኛ ፎቶግራፍ (12,000 ብር)*\n"
            "__________________________\n\n"
            "• 100 የታተሙ ፎቶዎች\n"
            "• ሁሉም ፎቶዎች በሶፍት ኮፒ\n\n"
            "📸 *ስራዎቻችንን ይመልከቱ:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ፦: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'photo_premium': (
            "💎 *ፕሪሚየም ፎቶግራፍ (15,000 ብር)*\n"
            "__________________________\n\n"
            "• ላሚኔት የተደረገ አልበም\n"
            "• ሁሉም ፎቶዎች በሶፍት ኮፒ\n\n"
            "📸 *ስራዎቻችንን ይመልከቱ:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ፦: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        'videography': (
            "🎥 *የቪዲዮ አገልግሎት (15,000 ብር)*\n"
            "__________________________\n\n"
            "• ሙሉ የቪዲዮ ሽፋን \n"
            "• በባለሙያ ኤዲት የተደረገ ቪዲዮ\n\n"
            "📸 *ስራዎቻችንን ይመልከቱ:*\n"
            "[Instagram](https://instagram.com/agospostpartum) | "
            "[Website](https://www.agospostpartumcare.com/)\n\n"
            "👉 *ለተጨማሪ ቪዲዮዎች የቲክቶክ ገፃችንን ይጎብኙ፦: https://www.tiktok.com/@agos_postpartumcare*"
        ),
        
        'contact_text': (
            "📞 ••ያግኙን••\n\n"
            "⏰ •የስራ ሰዓት: 2፡00 ጥዋት - 2፡00 ማታ (በአካባቢው ሰዓት)\n"
            "⚠️ •ማሳሰቢያ: ከምሽቱ 2፡00 ሰዓት በፊት አይሰራም\n\n"
            "📞 ••ስልክ:•• \n\n"
            "📱 +251 967 621 545\n"
            "📱 +251 980 040 468\n\n"
            "🎵 •• የሶሻል ሚዲያ ገፃችንን ይጎብኙ :••\n"
            "📸 •ኢንስታግራም: (https://instagram.com/agos_postpartumcare)\n"
            "🎵 •ቲክቶክ: (https://www.tiktok.com/@Agos_postpartumCare)\n"
            "📱 •ቴሌግራም: (https://t.me/Agospostpartumcare0)\n"
            "🌐 •ዌብሳይት: [www.agospostpartumcare.com]\n"
            "📍 •አድራሻ: [ፒያሳ፣ አባት ኮሜርሻል](https://maps.app.goo.gl/mHDvo7CpFwUubWyx6)"
        ),
        'agree_btn': "እስማማለሁ ✅",
        'back': "🔙 ወደ ዋና ማውጫ",
        'change_lang': "🌍 Change Language / ቋንቋ ቀይር",
        'q_back': "⬅️ ወደ ኋላ ተመለስ",
        
        # Dynamic Discover More messages (Amharic)
        'discover_after_decor': (
            "✨ የዲኮር ትዕዛዝዎ እስከሚረጋገጥ ድረስ ተጨማሪ አገልግሎቶችን ከፈለጉ ይምረጡ ✨\n\n"
            "🚗 •የሊሙዚን አገልግሎት - በታላቅ አቀባበል ይግቡ\n"
            "📸 •የፎቶግራፍ አገልግሎቶች - ትዝታዎችን ይቅረጹ\n\n"
            "ለማዘዝ ከታች ይጫኑ!"
        ),
        'discover_after_limo': (
            "✨ የሊሙዚን ትዕዛዝዎ እስከሚረጋገጥ ድረስ ተጨማሪ አገልግሎቶችን ከፈለጉ ይምረጡ✨\n\n"
            "🎁 •የዲኮር ፓኬጆች - ውብ ቦታ ይፍጠሩ\n"
            "📸 •የፎቶግራፍ አገልግሎቶች - ትዝታዎችን ይቅረጹ\n\n"
            "ለማዘዝ ከታች ይጫኑ!"
        ),
        'discover_after_photo': (
            "✨ የፎቶግራፍ ትዕዛዝዎ እስከሚረጋገጥ ድረስ ተጨማሪ አገልግሎቶችን ከፈለጉ ይምረጡ✨\n\n"
            "🎁 •የዲኮር ፓኬጆች - ውብ ቦታ ይፍጠሩ\n"
            "🚗 •የሊሙዚን አገልግሎት - በታላቅ አቀባበል ይግቡ\n\n"
            "ለማዘዝ ከታች ይጫኑ!"
        ),
        'discover_complete': (
            "🎉 ሁሉንም አገልግሎቶቻችንን ተመልክተዋል! 🎉\n\n"
            "AGOSን በመምረጥዎ እናመሰግናለን። ያዘዙት አገልግሎት፦\n"
            "{booked_services}\n\n"
            "ተጨማሪ ማከል ይፈልጋሉ? ለልዩ ፓኬጆች ያግኙን!\n\n"
            "📞 •ያግኙን: @agos_postpartumcare\n"
            "📱 •ስልክ: +251 967 621 545"
            "📱 •ስልክ: +251 967 621 545"
        ),
        'book_now': "📝 አሁን ይዘዙ"
    }
}

# --- PDF GENERATOR FUNCTIONS ---
# --- PDF GENERATOR FUNCTIONS (FORMAL VERSION WITH CORRECT BANK DETAILS) ---
def create_decor_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add logo if exists
    if os.path.exists(LOGO_PATH):
        try:
            logo = ImageReader(LOGO_PATH)
            c.drawImage(logo, 450, height - 90, width=80, height=80, mask='auto')
        except Exception:
            pass

    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 50, "AGOS POSTPARTUM CARE")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 80, "DECOR SERVICE")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 105, "OFFICIAL BOOKING CONFIRMATION")
    
    # Line separator
    c.line(50, height - 120, 550, height - 120)
    
    # Booking reference and date
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 140, f"Booking Reference: DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    c.drawString(50, height - 155, f"Date of Issue: {datetime.now().strftime('%B %d, %Y')}")
    c.drawString(50, height - 170, f"Time of Issue: {datetime.now().strftime('%H:%M:%S')}")
    
    c.line(50, height - 180, 550, height - 180)

    # Client Information Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 200, "1. CLIENT INFORMATION")
    c.setFont("Helvetica", 11)
    y_position = height - 225

    # Format each field properly with formal labels
    field_mappings = {
        'd_name': 'Full Name',
        'd_gender': 'Gender of Newborn',
        'd_phone': 'Primary Contact Number',
        'd_username': 'Telegram Username',
        'd_contact': 'Alternative Contact Number'
    }

    for key, value in data.items():
        if key.startswith('d_') and key in field_mappings:
            label = field_mappings[key]
            c.drawString(70, y_position, f"{label}: {value}")
            y_position -= 20
            
            if y_position < 300:
                c.showPage()
                y_position = height - 100
                c.setFont("Helvetica", 11)

    # Service Details Section
    y_position -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "2. SERVICE DETAILS")
    y_position -= 25
    c.setFont("Helvetica", 11)
    
    service_mappings = {
        'd_addr': 'Service Address',
        'd_house': 'House Type',
        'd_pkg': 'Selected Package',
        'd_date': 'Preferred Date & Time',
        'd_notes': 'Special Requests / Notes'
    }
    
    for key, value in data.items():
        if key.startswith('d_') and key in service_mappings:
            label = service_mappings[key]
            # Handle long text
            text = f"{label}: {value if value else 'None provided'}"
            if len(text) > 80:
                c.drawString(70, y_position, f"{label}:")
                y_position -= 18
                # Word wrap for long values
                words = str(value).split()
                line = ""
                for word in words:
                    test_line = line + " " + word if line else word
                    if c.stringWidth(test_line, "Helvetica", 11) < 450:
                        line = test_line
                    else:
                        c.drawString(90, y_position, line)
                        y_position -= 18
                        line = word
                if line:
                    c.drawString(90, y_position, line)
                    y_position -= 20
            else:
                c.drawString(70, y_position, text)
                y_position -= 20
            
            if y_position < 150:
                c.showPage()
                y_position = height - 100

    # Payment Information Section
    if y_position < 200:
        c.showPage()
        y_position = height - 100
    
    y_position -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "3. PAYMENT INFORMATION")
    y_position -= 25
    c.setFont("Helvetica", 11)
    c.drawString(70, y_position, "Payment Status: PENDING - Awaiting 50% Deposit Confirmation")
    y_position -= 20
    c.drawString(70, y_position, "Bank: Commercial Bank of Ethiopia (CBE)")
    y_position -= 20
    c.drawString(70, y_position, "Account Name: Sara Mohammed")
    y_position -= 20
    c.drawString(70, y_position, "Account Number: 1000505694407")
    y_position -= 20
    c.drawString(70, y_position, "Required Deposit: 50% of total package price")

    # Terms and Conditions
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "4. TERMS AND CONDITIONS")
    y_position -= 20
    c.setFont("Helvetica", 9)
    c.drawString(70, y_position, "• This booking is provisional until payment confirmation is received.")
    y_position -= 15
    c.drawString(70, y_position, "• The 50% deposit must be paid within 24 hours to secure your booking.")
    y_position -= 15
    c.drawString(70, y_position, "• Remaining balance is due on the day of service.")
    y_position -= 15
    c.drawString(70, y_position, "• Cancellations made less than 48 hours before the event may incur charges.")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 50, "This is an official document generated by AGOS Postpartum Care Telegram Bot.")
    c.drawString(50, 40, "For any inquiries, please contact: +251 967 621 545 | +251 980 040 468")
    c.drawString(50, 30, "Website: www.agospostpartumcare.com | Email: info@agospostpartumcare.com")
    
    c.save()
    buffer.seek(0)
    return buffer


def create_limo_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    if os.path.exists(LOGO_PATH):
        try:
            logo = ImageReader(LOGO_PATH)
            c.drawImage(logo, 450, height - 90, width=80, height=80, mask='auto')
        except Exception:
            pass

    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 50, "AGOS POSTPARTUM CARE")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 80, "LIMOUSINE SERVICE")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 105, "OFFICIAL BOOKING CONFIRMATION")
    
    c.line(50, height - 120, 550, height - 120)
    
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 140, f"Booking Reference: LIM-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    c.drawString(50, height - 155, f"Date of Issue: {datetime.now().strftime('%B %d, %Y')}")
    c.drawString(50, height - 170, f"Time of Issue: {datetime.now().strftime('%H:%M:%S')}")
    
    c.line(50, height - 180, 550, height - 180)

    # Client Information Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 200, "1. CLIENT INFORMATION")
    c.setFont("Helvetica", 11)
    y_position = height - 225

    field_mappings = {
        'l_name': 'Full Name',
        'l_phone': 'Contact Number'
    }

    for key, value in data.items():
        if key.startswith('l_') and key in field_mappings:
            label = field_mappings[key]
            c.drawString(70, y_position, f"{label}: {value}")
            y_position -= 20

    # Service Details Section
    y_position -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "2. SERVICE DETAILS")
    y_position -= 25
    c.setFont("Helvetica", 11)
    
    service_mappings = {
        'l_date': 'Scheduled Date & Time',
        'l_addr': 'Pickup & Destination Address',
        'l_package': 'Selected Package'
    }
    
    for key, value in data.items():
        if key.startswith('l_') and key in service_mappings:
            label = service_mappings[key]
            c.drawString(70, y_position, f"{label}: {value}")
            y_position -= 20

    # Payment Information Section
    if y_position < 200:
        c.showPage()
        y_position = height - 100
    
    y_position -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "3. PAYMENT INFORMATION")
    y_position -= 25
    c.setFont("Helvetica", 11)
    c.drawString(70, y_position, "Payment Status: PENDING - Awaiting 50% Deposit Confirmation")
    y_position -= 20
    c.drawString(70, y_position, "Bank: Commercial Bank of Ethiopia (CBE)")
    y_position -= 20
    c.drawString(70, y_position, "Account Name: Sara Mohammed")
    y_position -= 20
    c.drawString(70, y_position, "Account Number: 1000505694407")
    y_position -= 20
    c.drawString(70, y_position, "Required Deposit: 50% of total package price")

    # Terms and Conditions 
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "4. TERMS AND CONDITIONS")
    y_position -= 20
    c.setFont("Helvetica", 9)
    c.drawString(70, y_position, "• This booking is provisional until payment confirmation is received.")
    y_position -= 15
    c.drawString(70, y_position, "• The 50% deposit must be paid within 24 hours to secure your booking.")
    y_position -= 15
    c.drawString(70, y_position, "• Remaining balance is due on the day of service.")
    y_position -= 15
    c.drawString(70, y_position, "• Cancellations made less than 48 hours before the event may incur charges.")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 50, "This is an official document generated by AGOS Postpartum Care Telegram Bot.")
    c.drawString(50, 40, "For any inquiries, please contact: +251 967 621 545 | +251 980 040 468")
    c.drawString(50, 30, "Website: www.agospostpartumcare.com | Email: info@agospostpartumcare.com")
    
    c.save()
    buffer.seek(0)
    return buffer


def create_photo_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    if os.path.exists(LOGO_PATH):
        try:
            logo = ImageReader(LOGO_PATH)
            c.drawImage(logo, 450, height - 90, width=80, height=80, mask='auto')
        except Exception:
            pass

    # Header
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, height - 50, "AGOS POSTPARTUM CARE")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 80, "PHOTOGRAPHY & VIDEOGRAPHY SERVICES")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 105, "OFFICIAL BOOKING CONFIRMATION")
    
    c.line(50, height - 120, 550, height - 120)
    
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 140, f"Booking Reference: PHOTO-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    c.drawString(50, height - 155, f"Date of Issue: {datetime.now().strftime('%B %d, %Y')}")
    c.drawString(50, height - 170, f"Time of Issue: {datetime.now().strftime('%H:%M:%S')}")
    
    c.line(50, height - 180, 550, height - 180)

    # Client Information Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 200, "1. CLIENT INFORMATION")
    c.setFont("Helvetica", 11)
    y_position = height - 225

    field_mappings = {
        'ph_name': 'Full Name',
        'ph_phone': 'Contact Number'
    }

    for key, value in data.items():
        if key.startswith('ph_') and key in field_mappings:
            label = field_mappings[key]
            c.drawString(70, y_position, f"{label}: {value}")
            y_position -= 20

    # Service Details Section
    y_position -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "2. SERVICE DETAILS")
    y_position -= 25
    c.setFont("Helvetica", 11)
    
    service_mappings = {
        'ph_date': 'Event Date & Time',
        'ph_addr': 'Event Address',
        'ph_package': 'Selected Package'
    }
    
    for key, value in data.items():
        if key.startswith('ph_') and key in service_mappings:
            label = service_mappings[key]
            c.drawString(70, y_position, f"{label}: {value}")
            y_position -= 20

    # Payment Information Section
    if y_position < 200:
        c.showPage()
        y_position = height - 100
    
    y_position -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y_position, "3. PAYMENT INFORMATION")
    y_position -= 25
    c.setFont("Helvetica", 11)
    c.drawString(70, y_position, "Payment Status: PENDING - Awaiting 50% Deposit Confirmation")
    y_position -= 20
    c.drawString(70, y_position, "Bank: Commercial Bank of Ethiopia (CBE)")
    y_position -= 20
    c.drawString(70, y_position, "Account Name: Sara Mohammed")
    y_position -= 20
    c.drawString(70, y_position, "Account Number: 1000505694407")
    y_position -= 20
    c.drawString(70, y_position, "Required Deposit: 50% of total package price")

    # Terms and Conditions
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, "4. TERMS AND CONDITIONS")
    y_position -= 20
    c.setFont("Helvetica", 9)
    c.drawString(70, y_position, "• This booking is provisional until payment confirmation is received.")
    y_position -= 15
    c.drawString(70, y_position, "• The 50% deposit must be paid within 24 hours to secure your booking.")
    y_position -= 15
    c.drawString(70, y_position, "• Remaining balance is due on the day of service.")
    y_position -= 15
    c.drawString(70, y_position, "• Cancellations made less than 48 hours before the event may incur charges.")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 50, "This is an official document generated by AGOS Postpartum Care Telegram Bot.")
    c.drawString(50, 40, "For any inquiries, please contact: +251 967 621 545 | +251 980 040 468")
    c.drawString(50, 30, "Website: www.agospostpartumcare.com | Email: info@agospostpartumcare.com")
    
    c.save()
    buffer.seek(0)
    return buffer

# --- HELPERS ---
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

# --- DYNAMIC DISCOVER MORE FUNCTION ---
async def show_discover_more(update: Update, context: ContextTypes.DEFAULT_TYPE, last_booking_type=None):
    """Show dynamic discover more page based on what user has already booked"""
    lang = context.user_data.get('lang', 'en')
    
    # Track booked services in user_data
    booked_services = context.user_data.get('booked_services', [])
    if last_booking_type and last_booking_type not in booked_services:
        booked_services.append(last_booking_type)
        context.user_data['booked_services'] = booked_services
    
    # Determine which services are still available
    all_services = ['decor', 'limo', 'photo']
    available_services = [s for s in all_services if s not in booked_services]
    
    # Build buttons for available services
    discover_buttons = []
    
    if 'decor' in available_services:
        discover_buttons.append([InlineKeyboardButton("🎁 Book Decor / ዲኮር ይዘዙ", callback_data='show_decor_packages')])
    if 'limo' in available_services:
        discover_buttons.append([InlineKeyboardButton("🚗 Book Limousine / ሊሙዚን ይዘዙ", callback_data='show_limo_packages')])
    if 'photo' in available_services:
        discover_buttons.append([InlineKeyboardButton("📸 Book Photography / የፎቶግራፍ አገልግሎት ይዘዙ", callback_data='show_photo_packages')])
    
    # Add menu button
    discover_buttons.append([InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')])
    
    # Select appropriate message based on what's available
    if len(available_services) == 2:
        if 'decor' not in available_services:  # Decor already booked
            message = CONTENT[lang]['discover_after_decor']
        elif 'limo' not in available_services:  # Limo already booked
            message = CONTENT[lang]['discover_after_limo']
        else:  # Photo already booked
            message = CONTENT[lang]['discover_after_photo']
    elif len(available_services) == 1:
        # All but one service booked - show appropriate message
        if 'decor' in available_services:
            message = "Why not add beautiful decor to complete your celebration? / ዝግጅታችሁን ለማስዋብ ዲኮር አሁን ይዘዙ!"
        elif 'limo' in available_services:
            message = "Make a grand entrance with our limousine service! / በሊሙዚን አገልግሎታችን በታላቅ አቀባበል ይግቡ!"
        else:
            message = "Capture every moment with our photography! / ትዝታዎችን በፎቶግራፍ ይቅረጹ!"
    elif len(available_services) == 0:
        # All services booked!
        booked_list = "\n".join([f"✓ {s.title()}" for s in booked_services])
        message = CONTENT[lang]['discover_complete'].format(booked_services=booked_list)
        # Remove menu button and add contact button
        discover_buttons = [
            [InlineKeyboardButton("📞 Contact Us / ያግኙን", callback_data='info_contact')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
    else:
        # Default (2 services available) - show generic explore message
        message = "Explore our other services! / ሌሎች አገልግሎቶቻችንን ይመልከቱ!"
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(discover_buttons)
    )

# --- PACKAGE DISPLAY FUNCTIONS ---
# --- PACKAGE DISPLAY FUNCTIONS ---
async def show_decor_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Correctly identify the user's language
    lang = context.user_data.get('lang', 'en')
    
    # Debug prints to verify
    print(f"🔍 DEBUG - Showing decor packages in language: {lang}")
    print(f"🔍 DEBUG - Amharic decor_basic exists: {'decor_basic' in CONTENT['am']}")
    
    # Pull the pieces from your dictionary
    basic = CONTENT[lang]['decor_basic']
    deluxe = CONTENT[lang]['decor_deluxe']
    premium = CONTENT[lang]['decor_premium']
    
    # Combine them into one text string based on language
    if lang == 'en':
        text = (
            f"{basic}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{deluxe}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{premium}\n\n"
            "👇 *Choose a package to book:*"
        )
    else:
        text = (
            f"{basic}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{deluxe}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{premium}\n\n"
            "👇 *ለማዘዝ አንዱን ይምረጡ፦*"
        )

    # Dynamic buttons that change based on language
    if lang == 'en':
        kb = [
            [InlineKeyboardButton("📝 Book 🔸 Basic - 15,000 ETB", callback_data='d_start_basic')],
            [InlineKeyboardButton("📝 Book 💎 Deluxe - 20,000 ETB", callback_data='d_start_deluxe')],
            [InlineKeyboardButton("📝 Book 👑 Premium - 25,000 ETB", callback_data='d_start_premium')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
    else:
        kb = [
            [InlineKeyboardButton("🔸 መደበኛ - 15,000 ETB ይዘዙ", callback_data='d_start_basic')],
            [InlineKeyboardButton("💎 ደልክስ - 20,000 ETB ይዘዙ", callback_data='d_start_deluxe')],
            [InlineKeyboardButton("👑 ፕሪሚየም - 25,000 ETB ይዘዙ", callback_data='d_start_premium')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
    
    try:
        # We use Markdown because your content uses [video](link)
        await query.message.edit_text(
            text, 
            reply_markup=InlineKeyboardMarkup(kb), 
            parse_mode='Markdown', 
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Markdown error: {e}")
        # Fallback: if there's any weird character, show it as plain text
        await query.message.edit_text(
            text, 
            reply_markup=InlineKeyboardMarkup(kb), 
            disable_web_page_preview=True
        )

async def show_limo_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    text = (
        f"{CONTENT[lang]['limo_grand']}\n\n"
        "__________________________\n\n"
        f"{CONTENT[lang]['limo_special']}\n\n"
        "__________________________\n\n"
        f"{CONTENT[lang]['limo_royal']}"
    )

    if lang == 'en':
        kb = [
            [InlineKeyboardButton("⭐ Book ⭐ Grand Arrival - 25,000 ETB", callback_data='l_start_grand')],
            [InlineKeyboardButton("✨ Book ✨ Special Arrival - 30,000 ETB", callback_data='l_start_special')],
            [InlineKeyboardButton("👑 Book 👑 Royal Welcome - 35,000 ETB", callback_data='l_start_royal')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
    else:
        kb = [
            [InlineKeyboardButton("⭐ መደበኛ - 25,000 ETB ይዘዙ", callback_data='l_start_grand')],
            [InlineKeyboardButton("✨ ልዩ - 30,000 ETB ይዘዙ", callback_data='l_start_special')],
            [InlineKeyboardButton("👑 ሮያል - 35,000 ETB ይዘዙ", callback_data='l_start_royal')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
    
    try:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown', disable_web_page_preview=True)
    except Exception:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)

async def show_photo_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    text = (
        f"{CONTENT[lang]['photo_digital']}\n\n"
        f"{CONTENT[lang]['photo_standard']}\n\n"
        f"{CONTENT[lang]['photo_premium']}\n\n"
        f"{CONTENT[lang]['videography']}"
    )

    if lang == 'en':
        kb = [
            [InlineKeyboardButton("📱 Book 📱 Digital Photo - 10,000 ETB", callback_data='ph_start_digital')],
            [InlineKeyboardButton("🖼️ Book 🖼️ Standard Photo - 12,000 ETB", callback_data='ph_start_standard')],
            [InlineKeyboardButton("💎 Book 💎 Premium Photo - 15,000 ETB", callback_data='ph_start_premium')],
            [InlineKeyboardButton("🎥 Book 🎥 Videography - 15,000 ETB", callback_data='ph_start_video')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
    else:
        kb = [
            [InlineKeyboardButton("📱 ዲጂታል - 10,000 ETB ይዘዙ", callback_data='ph_start_digital')],
            [InlineKeyboardButton("🖼️ መደበኛ - 12,000 ETB ይዘዙ", callback_data='ph_start_standard')],
            [InlineKeyboardButton("💎 ፕሪሚየም - 15,000 ETB ይዘዙ", callback_data='ph_start_premium')],
            [InlineKeyboardButton("🎥 ቪዲዮ - 15,000 ETB ይዘዙ", callback_data='ph_start_video')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
        ]
    
    try:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown', disable_web_page_preview=True)
    except Exception:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)

# --- INDIVIDUAL PACKAGE VIEW FUNCTIONS ---
async def view_decor_basic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='d_start_basic')],
        [InlineKeyboardButton(back_text, callback_data='show_decor_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='d_start_deluxe')],
        [InlineKeyboardButton(back_text, callback_data='show_decor_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='d_start_premium')],
        [InlineKeyboardButton(back_text, callback_data='show_decor_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='l_start_grand')],
        [InlineKeyboardButton(back_text, callback_data='show_limo_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='l_start_special')],
        [InlineKeyboardButton(back_text, callback_data='show_limo_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='l_start_royal')],
        [InlineKeyboardButton(back_text, callback_data='show_limo_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_digital')],
        [InlineKeyboardButton(back_text, callback_data='show_photo_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_standard')],
        [InlineKeyboardButton(back_text, callback_data='show_photo_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_premium')],
        [InlineKeyboardButton(back_text, callback_data='show_photo_packages')],
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
    
    back_text = "🔙 Back to Packages" if lang == 'en' else "🔙 ወደ ፓኬጆች ተመለስ"
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='ph_start_video')],
        [InlineKeyboardButton(back_text, callback_data='show_photo_packages')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['videography'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )



# --- DECOR BOOKING FLOW ---
async def d_start(update: Update, context: ContextTypes.DEFAULT_TYPE, package=None):
    """Start decor booking flow with optional package pre-selection"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    # Store selected package if coming from package view
    if package:
        context.user_data['d_pkg'] = package
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_decor_packages')]
    ])
    
    await query.message.reply_text(
        "🎁 **Decor Booking / ዲኮር ለማዘዝ**\n\n1. Full Name / ሙሉ ስም:",
        reply_markup=kb
    )
    return D_NAME

async def d_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    kb = [
        [InlineKeyboardButton("Male / ወንድ", callback_data='Male'),
         InlineKeyboardButton("Female / ሴት", callback_data='Female')],
        [InlineKeyboardButton("Not Sure / እርግጠኛ አይደለሁም", callback_data='NotSure')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_decor_packages')]
    ]
    
    await update.message.reply_text(
        "2. Gender of the Newborn / የሕፃኑ ጾታ:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return D_GENDER

async def d_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['d_gender'] = query.data
    lang = context.user_data.get('lang', 'en')
    
    await query.message.reply_text(
        "3. House Address for Decor Setup / ዲኮር የሚሰራበት የቤት አድራሻ :",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_ADDR

async def d_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Client Phone Number / የደንበኛ ስልክ ቁጥር:",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_PHONE

async def d_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "5. Your Telegram Username (e.g., @username) / የቴሌግራም መለያዎ (ለምሳሌ፡ @username):",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_USERNAME

async def d_step5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_username'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "6. Alternative Phone Number / አማራጭ የስልክ ቁጥር:",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_CONTACT

async def d_step6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_contact'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    # If package wasn't pre-selected, show package selection
    if 'd_pkg' not in context.user_data:
        kb = [
            [InlineKeyboardButton("Basic - 15,000 ETB", callback_data='15k')],
            [InlineKeyboardButton("Deluxe - 20,000 ETB", callback_data='20k')],
            [InlineKeyboardButton("Premium - 25,000 ETB", callback_data='25k')],
            [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_decor_packages')]
        ]
        
        await update.message.reply_text(
            "7. Select your preferred Decor Package / የሚፈልጉትን የዲኮር ፓኬጅ ይምረጡ:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return D_PKG
    else:
        # Skip to next question if package already selected
        # Skip to next question if package already selected
        # Call d_step7 with the original update (message) so the message-path is used
        return await d_step7(update, context)

async def d_step7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle both callback query and message cases
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data != 'd_back':
            context.user_data['d_pkg'] = query.data
        lang = context.user_data.get('lang', 'en')
        await query.message.reply_text(
            "8. Preferred Date & Time for the Decor setup (e.g., Morning 4:00 AM)\nFormat: (dd/mm/yyyy), (Time)\n\n"
            "8. ዲኮሩን የሚፈልጉበት ቀን እና ሰአት (ለምሳሌ፡ ጥዋት 4፡00)\nቅርጸት: (ቀን/ወር/ዓመት), (ሰዓት)",
            reply_markup=get_nav_kb(lang, back_callback='d_back')
        )
    else:
        # This is a message object (from skip case)
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "8. Preferred Date & Time for the Decor setup (e.g., 21/08/2018, Morning 4:00 AM)\n\n"
            "8. ዲኮሩን የሚፈልጉበት ቀን እና ሰአት (ለምሳሌ፡ 21/08/2018, ጥዋት 4፡00)\n",
            reply_markup=get_nav_kb(lang, back_callback='d_back')
        )
    return D_DATE

async def d_step8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')

    kb = [
        [InlineKeyboardButton("Villa / ቪላ", callback_data='Villa'),
         InlineKeyboardButton("Apartment / አፓርትመንት", callback_data='Apartment')],
        [InlineKeyboardButton("Condominium / ኮንዶሚየም", callback_data='Condominium')],
        [InlineKeyboardButton("G+1", callback_data='G1'),
         InlineKeyboardButton("G+2", callback_data='G2')],
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='d_back')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_decor_packages')]
    ]

    await update.message.reply_text(
        "9. House Type / የቤት አይነት:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return D_HOUSE

async def d_step9(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')

    if query.data == 'd_back':
        # Go back to previous question
        return await d_step8(update, context)

    context.user_data['d_house'] = query.data
    
    warning_msg = (
        "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
            "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
            "🏧 *Commercial Bank of Ethiopia (CBE) / የኢትዮጵያ ንግድ ባንክ *\n"
            "👤 Account Name: Sara Mohammed \n"
            "🔢 Account Number: 1000505694407\n\n"
            "💵 Amount: 50% of the selected package \n\n"
            "✅ After filling this form, please send a screenshot of your 50% deposit payment to confirm your booking.\n"
            "‼️ Note: Booking will not be considered complete until the deposit is received.\n\n"
            "✅ ይህንን ቅጽ ከሞሉ በኋላ፣ ትዕዛዝዎን ለማረጋገጥ የ50% የተቀማጭ ክፍያ ስክሪን ሾት ይላኩ።\n"
            "‼️ ማሳሰቢያ፡- ተቀማጭ ገንዘብ እስኪደርስ ድረስ ትዕዛዝዎ እንደተጠናቀቀ አይቆጠርም።\n"
    )
    
    await query.message.reply_text(warning_msg, parse_mode='Markdown')
    await query.message.reply_text(
        "10. Special Notes (Limousine, Photo, Video, or None) / ልዩ ማስታወሻ (ሊሙዚን፣ ፎቶ፣ ቪዲዮ፣ ወይም ምንም):",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_NOTES

async def d_step10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_notes'] = update.message.text
    lang = context.user_data.get('lang', 'en')

    await update.message.reply_text(
        "📤 Upload your Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
        reply_markup=get_nav_kb(lang, back_callback='d_back')
    )
    return D_PAYMENT

async def d_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo. / እባክዎ ፎቶ ይላኩ።",
            reply_markup=get_nav_kb(lang, back_callback='d_back')
        )
        return D_PAYMENT

    pay_img = update.message.photo[-1].file_id
    pdf_file = create_decor_pdf(context.user_data)

    # This MUST be indented inside the function
    summary = (
        f"🔔 *NEW DECOR SERVICE BOOKING / አዲስ የዲኮር ትዕዛዝ* 🔔\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Booking Reference:* DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}\n"
        f"*Booking Date:* {datetime.now().strftime('%B %d, %Y')}\n"
        f"*Booking Time:* {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"*1. CLIENT INFORMATION*\n"
        f"   • Full Name: {context.user_data.get('d_name')}\n"
        f"   • Baby Gender: {context.user_data.get('d_gender')}\n"
        f"   • Primary Contact: {context.user_data.get('d_phone')}\n"
        f"   • Telegram: {context.user_data.get('d_username')}\n"
        f"   • Alternative Contact: {context.user_data.get('d_contact')}\n\n"
        f"*2. SERVICE DETAILS*\n"
        f"   • Package: {context.user_data.get('d_pkg')}\n"
        f"   • Service Address: {context.user_data.get('d_addr')}\n"
        f"   • House Type: {context.user_data.get('d_house')}\n"
        f"   • Preferred Date: {context.user_data.get('d_date')}\n"
        f"   • Special Requests: {context.user_data.get('d_notes') or 'None'}\n\n"
        f"*3. PAYMENT INFORMATION*\n"
        f"   • Bank: Commercial Bank of Ethiopia (CBE)\n"
        f"   • Account Name: Sara Mohammed\n"
        f"   • Account Number: 1000505694407\n"
        f"   • Required Deposit: 50% of package price\n"
        f"   • Status: PENDING - Payment Screenshot Received, Awaiting Verification\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Payment screenshot has been received.\n"
        f"⚠️ Please verify the payment and confirm the booking by contacting the client.\n"
        f"📱 Client Telegram: {context.user_data.get('d_username')}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=pay_img, caption=summary)
            pdf_file.seek(0)
            await context.bot.send_document(
                chat_id=admin_id, 
                document=pdf_file, 
                filename=f"Decor_{context.user_data.get('d_name','Booking')}.pdf"
            )
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")

    pdf_file.seek(0)
    # YOUR SIMPLE CAPTION - kept exactly as you want
    await update.message.reply_document(
        document=pdf_file, 
        filename="AGOS_Decor_Booking.pdf", 
        caption="✅ Your booking is awaiting confirmation. / ማረጋገጫ በመጠበቅ ላይ።"
    )

    await show_discover_more(update, context, 'decor')
    return ConversationHandler.END

async def d_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button in decor flow"""
    query = update.callback_query
    await query.answer()
    # This will be handled by the conversation handler's fallback
    return D_NAME

# --- LIMOUSINE BOOKING FLOW ---
async def l_start(update: Update, context: ContextTypes.DEFAULT_TYPE, package=None):
    """Start limousine booking flow with optional package pre-selection"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    if package:
        context.user_data['l_package'] = package
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_limo_packages')]
    ])
    
    await query.message.reply_text(
        "🚗 **Limousine Booking / ሊሙዚን ማዘዣ**\n\n1. Full Name / ሙሉ ስም:",
        reply_markup=kb
    )
    return L_NAME

async def l_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['l_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "2. Phone Number / ስልክ ቁጥር:",
        reply_markup=get_nav_kb(lang, back_callback='l_back')
    )
    return L_PHONE

async def l_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['l_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "3. Preferred Date & Time (e.g., 21/08/2018, Morning 4:00 AM)\n\n"
        "3. የሚፈለግ ቀን እና ሰዓት (ለምሳሌ፡ 21/08/2018, ጥዋት 4፡00)",
        reply_markup=get_nav_kb(lang, back_callback='l_back')
    )
    return L_DATE

async def l_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['l_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Pickup Address (የሚነሱበት አድራሻ) &  Destination (መዳረሻ / የቤትዎ አድራሻ)\n (ለምሳሌ፡ ከ 4 ኪሎ ሄመን ሆስፒታል ወደ ቃሊቲ) :",
        reply_markup=get_nav_kb(lang, back_callback='l_back')
    )
    return L_ADDR

async def l_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['l_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    # If package wasn't pre-selected, show package selection
    if 'l_package' not in context.user_data:
        kb = [
            [InlineKeyboardButton("Grand Arrival - 25,000 ETB", callback_data='l_25k'),
             InlineKeyboardButton("Special Arrival - 30,000 ETB", callback_data='l_30k')],
            [InlineKeyboardButton("Royal Welcome - 35,000 ETB", callback_data='l_35k')],
            [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='l_back')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_limo_packages')]
        ]
        
        await update.message.reply_text(
            "5. Select Package / ፓኬጅ ይምረጡ:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return L_PACKAGE
    else:
        # Skip to payment step
        return await l_step5(update, context)

async def l_step5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle both callback query and message cases
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data != 'l_back':
            context.user_data['l_package'] = query.data
        lang = context.user_data.get('lang', 'en')
        
        warning_msg = (
            "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
            "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
            "🏧 *Commercial Bank of Ethiopia (CBE) / የኢትዮጵያ ንግድ ባንክ *\n"
            "👤 Account Name: Sara Mohammed \n"
            "🔢 Account Number: 1000505694407\n\n"
            "💵 Amount: 50% of the selected package \n\n"
            "✅ After filling this form, please send a screenshot of your 50% deposit payment to confirm your booking.\n"
            "‼️ Note: Booking will not be considered complete until the deposit is received.\n\n"
            "✅ ይህንን ቅጽ ከሞሉ በኋላ፣ ትዕዛዝዎን ለማረጋገጥ የ50% የተቀማጭ ክፍያ ስክሪን ሾት ይላኩ።\n"
            "‼️ ማሳሰቢያ፡- ተቀማጭ ገንዘብ እስኪደርስ ድረስ ትዕዛዝዎ እንደተጠናቀቀ አይቆጠርም።\n"
        )
        
        await query.message.reply_text(warning_msg, parse_mode='Markdown')
        await query.message.reply_text(
            "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
            reply_markup=get_nav_kb(lang, back_callback='l_back')
        )
    else:
        # Handle case where we skip package selection (from pre-selected)
        lang = context.user_data.get('lang', 'en')
        warning_msg = (
            "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
            "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
            "🏧 *Commercial Bank of Ethiopia (CBE) / የኢትዮጵያ ንግድ ባንክ *\n"
            "👤 Account Name: Sara Mohammed \n"
            "🔢 Account Number: 1000505694407\n\n"
            "💵 Amount: 50% of the selected package \n\n"
            "✅ After filling this form, please send a screenshot of your 50% deposit payment to confirm your booking.\n"
            "‼️ Note: Booking will not be considered complete until the deposit is received.\n\n"
            "✅ ይህንን ቅጽ ከሞሉ በኋላ፣ ትዕዛዝዎን ለማረጋገጥ የ50% የተቀማጭ ክፍያ ስክሪን ሾት ይላኩ።\n"
            "‼️ ማሳሰቢያ፡- ተቀማጭ ገንዘብ እስኪደርስ ድረስ ትዕዛዝዎ እንደተጠናቀቀ አይቆጠርም።\n"
        )
        
        await update.message.reply_text(warning_msg, parse_mode='Markdown')
        await update.message.reply_text(
            "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
            reply_markup=get_nav_kb(lang, back_callback='l_back')
        )
    return L_PAYMENT

async def l_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo. / እባክዎ ፎቶ ይላኩ።",
            reply_markup=get_nav_kb(lang, back_callback='l_back')
        )
        return L_PAYMENT

    pay_img = update.message.photo[-1].file_id
    pdf_file = create_limo_pdf(context.user_data)

    # Summary for admin - properly indented inside function
    summary = (
        f"🔔 *NEW LIMOUSINE SERVICE BOOKING / አዲስ የሊሙዚን ትዕዛዝ* 🔔\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Booking Reference:* LIM-{datetime.now().strftime('%Y%m%d%H%M%S')}\n"
        f"*Booking Date:* {datetime.now().strftime('%B %d, %Y')}\n"
        f"*Booking Time:* {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"*1. CLIENT INFORMATION*\n"
        f"   • Full Name: {context.user_data.get('l_name')}\n"
        f"   • Contact Number: {context.user_data.get('l_phone')}\n\n"
        f"*2. SERVICE DETAILS*\n"
        f"   • Package: {context.user_data.get('l_package')}\n"
        f"   • Scheduled Date: {context.user_data.get('l_date')}\n"
        f"   • Pickup & Destination: {context.user_data.get('l_addr')}\n\n"
        f"*3. PAYMENT INFORMATION*\n"
        f"   • Bank: Commercial Bank of Ethiopia (CBE)\n"
        f"   • Account Name: Sara Mohammed\n"
        f"   • Account Number: 1000505694407\n"
        f"   • Required Deposit: 50% of package price\n"
        f"   • Status: PENDING - Payment Screenshot Received, Awaiting Verification\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Payment screenshot has been received.\n"
        f"⚠️ Please verify the payment and confirm the booking by contacting the client.\n"
        f"📱 Client Phone: {context.user_data.get('l_phone')}"
    )

    for admin_id in ADMIN_IDS:
        try:
            # Send plain text caption to avoid Markdown entity parsing issues
            await context.bot.send_photo(chat_id=admin_id, photo=pay_img, caption=summary)
            pdf_file.seek(0)
            await context.bot.send_document(
                chat_id=admin_id, 
                document=pdf_file, 
                filename=f"Limousine_{context.user_data.get('l_name','Booking')}.pdf"
            )
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")

    pdf_file.seek(0)
    # SIMPLE CAPTION for client - exactly as you want
    await update.message.reply_document(
        document=pdf_file, 
        filename="AGOS_Limousine_Booking.pdf", 
        caption="✅ Your booking is awaiting confirmation. / ማረጋገጫ በመጠበቅ ላይ።"
    )
    
    # Show dynamic discover more page
    await show_discover_more(update, context, 'limo')
    
    return ConversationHandler.END

async def l_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button in limousine flow"""
    query = update.callback_query
    await query.answer()
    return L_NAME

# --- PHOTOGRAPHY BOOKING FLOW ---
async def ph_start(update: Update, context: ContextTypes.DEFAULT_TYPE, package=None):
    """Start photography booking flow with optional package pre-selection"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    
    if package:
        context.user_data['ph_package'] = package
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_photo_packages')]
    ])
    
    await query.message.reply_text(
        "📸 **Photograph / videography Services Booking / የፎቶግራፍ አገልግሎት ማዘዣ**\n\n1. Full Name / ሙሉ ስም:",
        reply_markup=kb
    )
    return PH_NAME

async def ph_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ph_name'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "2. Phone Number / ስልክ ቁጥር:",
        reply_markup=get_nav_kb(lang, back_callback='ph_back')
    )
    return PH_PHONE

async def ph_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ph_phone'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "3. Event Date & Time (e.g., 21/08/2018, Morning 4:00 AM)\n\n"
        "3. የዝግጅቱ ቀን እና ሰዓት (ለምሳሌ፡ 21/08/2018, ጥዋት 4፡00)",
        reply_markup=get_nav_kb(lang, back_callback='ph_back')
    )
    return PH_DATE

async def ph_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ph_date'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    await update.message.reply_text(
        "4. Event Address / የዝግጅቱ አድራሻ:",
        reply_markup=get_nav_kb(lang, back_callback='ph_back')
    )
    return PH_ADDR

async def ph_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ph_addr'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    # If package wasn't pre-selected, show package selection
    if 'ph_package' not in context.user_data:
        kb = [
            [InlineKeyboardButton("Digital Photography - 10,000 ETB", callback_data='ph_10k')],
            [InlineKeyboardButton("Standard Photography - 12,000 ETB", callback_data='ph_12k')],
            [InlineKeyboardButton("Premium Photography - 15,000 ETB", callback_data='ph_15k')],
            [InlineKeyboardButton("Videography - 15,000 ETB", callback_data='ph_15k_vid')],
            [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='ph_back')],
            [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='show_photo_packages')]
        ]
        
        await update.message.reply_text(
            "5. Select Package / ፓኬጅ ይምረጡ:",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return PH_PACKAGE
    else:
        # Skip to payment step
        return await ph_step5(update, context)

async def ph_step5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle both callback query and message cases
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data != 'ph_back':
            context.user_data['ph_package'] = query.data
        lang = context.user_data.get('lang', 'en')
        
        warning_msg = (
            "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
            "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
            "🏧 *Commercial Bank of Ethiopia (CBE) / የኢትዮጵያ ንግድ ባንክ *\n"
            "👤 Account Name: Sara Mohammed \n"
            "🔢 Account Number: 1000505694407\n\n"
            "💵 Amount: 50% of the selected package \n\n"
            "✅ After filling this form, please send a screenshot of your 50% deposit payment to confirm your booking.\n"
            "‼️ Note: Booking will not be considered complete until the deposit is received.\n\n"
            "✅ ይህንን ቅጽ ከሞሉ በኋላ፣ ትዕዛዝዎን ለማረጋገጥ የ50% የተቀማጭ ክፍያ ስክሪን ሾት ይላኩ።\n"
            "‼️ ማሳሰቢያ፡- ተቀማጭ ገንዘብ እስኪደርስ ድረስ ትዕዛዝዎ እንደተጠናቀቀ አይቆጠርም።\n"
        )
        
        await query.message.reply_text(warning_msg, parse_mode='Markdown')
        await query.message.reply_text(
            "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
            reply_markup=get_nav_kb(lang, back_callback='ph_back')
        )
    else:
        # Handle case where we skip package selection (from pre-selected)
        lang = context.user_data.get('lang', 'en')
        warning_msg = (
            "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
            "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
            "🏧 *Commercial Bank of Ethiopia (CBE) / የኢትዮጵያ ንግድ ባንክ *\n"
            "👤 Account Name: Sara Mohammed \n"
            "🔢 Account Number: 1000505694407\n\n"
            "💵 Amount: 50% of the selected package \n\n"
            "✅ After filling this form, please send a screenshot of your 50% deposit payment to confirm your booking.\n"
            "‼️ Note: Booking will not be considered complete until the deposit is received.\n\n"
            "✅ ይህንን ቅጽ ከሞሉ በኋላ፣ ትዕዛዝዎን ለማረጋገጥ የ50% የተቀማጭ ክፍያ ስክሪን ሾት ይላኩ።\n"
            "‼️ ማሳሰቢያ፡- ተቀማጭ ገንዘብ እስኪደርስ ድረስ ትዕዛዝዎ እንደተጠናቀቀ አይቆጠርም።\n"
        )
        
        await update.message.reply_text(warning_msg, parse_mode='Markdown')
        await update.message.reply_text(
            "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
            reply_markup=get_nav_kb(lang, back_callback='ph_back')
        )
    return PH_PAYMENT

async def ph_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        lang = context.user_data.get('lang', 'en')
        await update.message.reply_text(
            "Please upload a photo. / እባክዎ ፎቶ ይላኩ።",
            reply_markup=get_nav_kb(lang, back_callback='ph_back')
        )
        return PH_PAYMENT

    pay_img = update.message.photo[-1].file_id
    pdf_file = create_photo_pdf(context.user_data)

    # Summary for admin - properly indented inside function
    summary = (
        f"🔔 *NEW PHOTOGRAPHY & VIDEOGRAPHY BOOKING / አዲስ የፎቶግራፍ ትዕዛዝ* 🔔\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Booking Reference:* PHOTO-{datetime.now().strftime('%Y%m%d%H%M%S')}\n"
        f"*Booking Date:* {datetime.now().strftime('%B %d, %Y')}\n"
        f"*Booking Time:* {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"*1. CLIENT INFORMATION*\n"
        f"   • Full Name: {context.user_data.get('ph_name')}\n"
        f"   • Contact Number: {context.user_data.get('ph_phone')}\n\n"
        f"*2. SERVICE DETAILS*\n"
        f"   • Package: {context.user_data.get('ph_package')}\n"
        f"   • Event Date: {context.user_data.get('ph_date')}\n"
        f"   • Event Address: {context.user_data.get('ph_addr')}\n\n"
        f"*3. PAYMENT INFORMATION*\n"
        f"   • Bank: Commercial Bank of Ethiopia (CBE)\n"
        f"   • Account Name: Sara Mohammed\n"
        f"   • Account Number: 1000505694407\n"
        f"   • Required Deposit: 50% of package price\n"
        f"   • Status: PENDING - Payment Screenshot Received, Awaiting Verification\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Payment screenshot has been received.\n"
        f"⚠️ Please verify the payment and confirm the booking by contacting the client.\n"
        f"📱 Client Phone: {context.user_data.get('ph_phone')}"
    )

    for admin_id in ADMIN_IDS:
        try:
            # Send plain text caption to avoid Markdown entity parsing issues
            await context.bot.send_photo(chat_id=admin_id, photo=pay_img, caption=summary)
            pdf_file.seek(0)
            await context.bot.send_document(
                chat_id=admin_id, 
                document=pdf_file, 
                filename=f"Photography_{context.user_data.get('ph_name','Booking')}.pdf"
            )
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")

    pdf_file.seek(0)
    # SIMPLE CAPTION for client - exactly as you want
    await update.message.reply_document(
        document=pdf_file, 
        filename="AGOS_Photography_Booking.pdf", 
        caption="✅ Your booking is awaiting confirmation. / ማረጋገጫ በመጠበቅ ላይ።"
    )
    
    # Show dynamic discover more page
    await show_discover_more(update, context, 'photo')
    
    return ConversationHandler.END

async def ph_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button in photography flow"""
    query = update.callback_query
    await query.answer()
    return PH_NAME

# --- NAVIGATION FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    return await working_hours_gate(update, context)

async def after_hours_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if lang:
        context.user_data['lang'] = lang
    else:
        lang = context.user_data.get('lang', 'en')

    btns = CONTENT[lang]['btns']
    keyboard = [
        [InlineKeyboardButton(btns[0], callback_data='show_decor_packages'), 
         InlineKeyboardButton(btns[1], callback_data='show_limo_packages')],
        [InlineKeyboardButton(btns[2], callback_data='show_photo_packages'), 
         InlineKeyboardButton(btns[3], callback_data='info_contact')],
        [InlineKeyboardButton(btns[4], callback_data='send_pdf')],
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

async def info_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact info page"""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'en')
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]])
    await query.message.edit_text(
        CONTENT[lang]['contact_text'], 
        reply_markup=back_btn
    )

# --- APP RUNNER ---
if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    # Package view handlers
    app.add_handler(CallbackQueryHandler(show_decor_packages, pattern='^show_decor_packages$'))
    app.add_handler(CallbackQueryHandler(show_limo_packages, pattern='^show_limo_packages$'))
    app.add_handler(CallbackQueryHandler(show_photo_packages, pattern='^show_photo_packages$'))
    
    # Individual package view handlers
    app.add_handler(CallbackQueryHandler(view_decor_basic, pattern='^view_decor_basic$'))
    app.add_handler(CallbackQueryHandler(view_decor_deluxe, pattern='^view_decor_deluxe$'))
    app.add_handler(CallbackQueryHandler(view_decor_premium, pattern='^view_decor_premium$'))
    
    app.add_handler(CallbackQueryHandler(view_limo_grand, pattern='^view_limo_grand$'))
    app.add_handler(CallbackQueryHandler(view_limo_special, pattern='^view_limo_special$'))
    app.add_handler(CallbackQueryHandler(view_limo_royal, pattern='^view_limo_royal$'))
    
    app.add_handler(CallbackQueryHandler(view_photo_digital, pattern='^view_photo_digital$'))
    app.add_handler(CallbackQueryHandler(view_photo_standard, pattern='^view_photo_standard$'))
    app.add_handler(CallbackQueryHandler(view_photo_premium, pattern='^view_photo_premium$'))
    app.add_handler(CallbackQueryHandler(view_videography, pattern='^view_videography$'))

    # Decor booking conversation handler with package pre-selection
    d_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(lambda u, c: d_start(u, c, '15k'), pattern='^d_start_basic$'),
            CallbackQueryHandler(lambda u, c: d_start(u, c, '20k'), pattern='^d_start_deluxe$'),
            CallbackQueryHandler(lambda u, c: d_start(u, c, '25k'), pattern='^d_start_premium$')
        ],
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
        fallbacks=[
            CommandHandler("start", start), 
            CallbackQueryHandler(show_menu, pattern='^menu$'), 
            CallbackQueryHandler(start, pattern='^restart$'),
            CallbackQueryHandler(d_back_handler, pattern='^d_back$')
        ],
        allow_reentry=True,
        name="decor_conversation"
    )

    # Limousine booking conversation handler with package pre-selection
    l_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(lambda u, c: l_start(u, c, 'l_25k'), pattern='^l_start_grand$'),
            CallbackQueryHandler(lambda u, c: l_start(u, c, 'l_30k'), pattern='^l_start_special$'),
            CallbackQueryHandler(lambda u, c: l_start(u, c, 'l_35k'), pattern='^l_start_royal$')
        ],
        states={
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step1)],
            L_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step2)],
            L_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step3)],
            L_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_step4)],
            L_PACKAGE: [CallbackQueryHandler(l_step5)],
            L_PAYMENT: [MessageHandler(filters.PHOTO, l_final)]
        },
        fallbacks=[
            CommandHandler("start", start), 
            CallbackQueryHandler(show_menu, pattern='^menu$'), 
            CallbackQueryHandler(start, pattern='^restart$'),
            CallbackQueryHandler(l_back_handler, pattern='^l_back$')
        ],
        allow_reentry=True,
        name="limo_conversation"
    )

    # Photography booking conversation handler with package pre-selection
    ph_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(lambda u, c: ph_start(u, c, 'ph_10k'), pattern='^ph_start_digital$'),
            CallbackQueryHandler(lambda u, c: ph_start(u, c, 'ph_12k'), pattern='^ph_start_standard$'),
            CallbackQueryHandler(lambda u, c: ph_start(u, c, 'ph_15k'), pattern='^ph_start_premium$'),
            CallbackQueryHandler(lambda u, c: ph_start(u, c, 'ph_15k_vid'), pattern='^ph_start_video$')
        ],
        states={
            PH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step1)],
            PH_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step2)],
            PH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step3)],
            PH_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, ph_step4)],
            PH_PACKAGE: [CallbackQueryHandler(ph_step5)],
            PH_PAYMENT: [MessageHandler(filters.PHOTO, ph_final)]
        },
        fallbacks=[
            CommandHandler("start", start), 
            CallbackQueryHandler(show_menu, pattern='^menu$'), 
            CallbackQueryHandler(start, pattern='^restart$'),
            CallbackQueryHandler(ph_back_handler, pattern='^ph_back$')
        ],
        allow_reentry=True,
        name="photo_conversation"
    )

    # Add all handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(after_hours_handler, pattern='^after_hours$'))
    app.add_handler(CallbackQueryHandler(lambda u, c: show_menu(u, c, u.callback_query.data.split('_')[1]), pattern='^lang_'))
    app.add_handler(CallbackQueryHandler(show_menu, pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(info_contact, pattern='^info_contact$'))
    app.add_handler(CallbackQueryHandler(send_services_pdf, pattern='^send_pdf$'))
    app.add_handler(CallbackQueryHandler(start, pattern='^restart$'))
    
    app.add_handler(d_conv)
    app.add_handler(l_conv)
    app.add_handler(ph_conv)

    print("🎨 AGOS Enhanced Services Bot is live with FIXED conversation flows!")
    print(f"⏰ Working hours: {WORKING_HOURS_START}:00 - {WORKING_HOURS_END}:00 LT")
    print("📱 Features: Individual package pages with booking buttons, smart discover more")
    print("✅ All booking forms should now work correctly!")
    app.run_polling()
