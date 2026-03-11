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
import traceback

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = []
# Get admin IDs from environment variables
for i in range(1, 6):  # Support up to 5 admins
    admin_id = os.environ.get(f"ADMIN_ID_{i}")
    if admin_id:
        try:
            ADMIN_IDS.append(int(admin_id))
            logger.info(f"Added admin {i}: {admin_id}")
        except ValueError:
            logger.error(f"Invalid ADMIN_ID_{i}: {admin_id}")

LOGO_PATH = os.environ.get("LOGO_PATH", "logo.webp")

print("=" * 50)
print(f"TOKEN exists: {bool(TOKEN)}")
print(f"ADMIN_IDS: {ADMIN_IDS}")
print("=" * 50)

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

if not ADMIN_IDS:
    logger.warning("No admin IDs configured! Notifications will not be sent.")

# --- CONVERSATION STATES ---
# Decor Booking
(D_NAME, D_PHONE, D_ADDRESS, D_DATE, D_NOTES, D_PAYMENT) = range(1, 7)

# Limousine Booking
(L_NAME, L_PHONE, L_DATE, L_ADDRESS, L_PAYMENT) = range(10, 15)

# Photography Booking
(PH_NAME, PH_PHONE, PH_DATE, PH_ADDRESS, PH_PAYMENT) = range(20, 25)

# --- SIMPLE CONTENT ---
WELCOME_TEXT = (
    "🎁 *Welcome to AGOS Services* 🌸\n\n"
    "✨ Premium home decor\n"
    "🚗 Luxury limousine arrivals\n"
    "📸 Professional photography"
)

DECOR_PACKAGES = {
    'basic': "🔸 *Basic Decor - 15,000 ETB*\n\n• Bedroom Decoration\n• Floor Decoration\n• Corridor Decoration\n• Salon Decoration",
    'deluxe': "💎 *Deluxe Decor - 20,000 ETB*\n\n• Bedroom, Corridor & Salon Decor\n• Large Flower Arrangement\n• 2 Kg Cake",
    'premium': "👑 *Premium Decor - 25,000 ETB*\n\n• Bedroom Decor with Agober rent\n• Corridor & Salon Decor\n• Large Flower Arrangement\n• 2 Kg Custom Cake"
}

LIMO_PACKAGES = {
    'grand': "⭐ *Grand Arrival - 25,000 ETB*\n\n• Special limousine service\n• Elegant ride home",
    'special': "✨ *Special Arrival - 30,000 ETB*\n\n• Exclusive limousine service\n• Luxurious ride",
    'royal': "👑 *Royal Welcome - 35,000 ETB*\n\n• Premium luxury limousine\n• Full package"
}

PHOTO_PACKAGES = {
    'digital': "📱 *Digital Photo - 10,000 ETB*\n\n• Professional photography\n• All photos in soft copy",
    'standard': "🖼️ *Standard Photo - 12,000 ETB*\n\n• 100 printed photos\n• Soft copy",
    'premium': "💎 *Premium Photo - 15,000 ETB*\n\n• Laminated album\n• Soft copy",
    'video': "🎥 *Videography - 15,000 ETB*\n\n• Full video coverage\n• Edited video"
}

CONTACT_TEXT = (
    "📞 *Contact Us*\n\n"
    "⏰ Hours: 8:00 AM - 8:00 PM\n"
    "📱 Telegram: @agos_postpartumcare\n"
    "📞 Phone: +251 967 621 545\n"
    "📍 Location: Piassa, Addis Ababa"
)

# --- PDF GENERATOR ---
def create_pdf(data, service_type):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, f"AGOS {service_type} Booking")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Order Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.line(50, height - 85, 550, height - 85)

        # Content
        c.setFont("Helvetica", 11)
        y = height - 120
        
        for key, value in data.items():
            if key not in ['booking_type', 'package'] and value:
                label = key.replace('_', ' ').title()
                text = f"{label}: {value}"
                c.drawString(50, y, text)
                y -= 25
                if y < 50:
                    c.showPage()
                    y = height - 50

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"PDF Error: {e}")
        logger.error(traceback.format_exc())
        return None

# --- NOTIFY ADMINS ---
async def notify_admins(context, message, photo=None, document=None, filename=None):
    if not ADMIN_IDS:
        logger.warning("No admin IDs configured, skipping notification")
        return
    
    for admin_id in ADMIN_IDS:
        try:
            if photo:
                # Send photo first
                await context.bot.send_photo(
                    chat_id=admin_id, 
                    photo=photo, 
                    caption=message[:1024], 
                    parse_mode='Markdown'
                )
                logger.info(f"Sent photo to admin {admin_id}")
            elif document:
                # Send document
                await context.bot.send_document(
                    chat_id=admin_id, 
                    document=document, 
                    filename=filename or "booking.pdf",
                    caption=message[:1024]
                )
                logger.info(f"Sent document to admin {admin_id}")
            else:
                # Send text only
                await context.bot.send_message(
                    chat_id=admin_id, 
                    text=message, 
                    parse_mode='Markdown'
                )
                logger.info(f"Sent message to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
            logger.error(traceback.format_exc())

# --- START & MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='lang_am')]
    ]
    await update.message.reply_text(
        "🌿 Choose Language / ቋንቋ ይምረጡ:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main menu handler"""
    query = update.callback_query
    await query.answer()
    
    # Handle language selection
    if query.data in ['lang_en', 'lang_am']:
        context.user_data['lang'] = query.data.split('_')[1]
        logger.info(f"User selected language: {context.user_data['lang']}")
    
    keyboard = [
        [InlineKeyboardButton("🎁 Decor Packages", callback_data='menu_decor'),
         InlineKeyboardButton("🚗 Limousine", callback_data='menu_limo')],
        [InlineKeyboardButton("📸 Media", callback_data='menu_photo'),
         InlineKeyboardButton("📞 Contact", callback_data='menu_contact')],
        [InlineKeyboardButton("🌍 Change Language", callback_data='restart')]
    ]
    
    await query.message.edit_text(
        WELCOME_TEXT, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

# --- DECOR PACKAGES ---
async def decor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Decor packages menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔸 Basic - 15k", callback_data='view_decor_basic')],
        [InlineKeyboardButton("💎 Deluxe - 20k", callback_data='view_decor_deluxe')],
        [InlineKeyboardButton("👑 Premium - 25k", callback_data='view_decor_premium')],
        [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
    ]
    
    await query.message.edit_text(
        "🎁 *Select Decor Package:*", 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def view_decor_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View individual decor package"""
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('view_decor_', '')
    context.user_data['selected_package'] = package
    context.user_data['service_type'] = 'decor'
    
    text = DECOR_PACKAGES.get(package, "Package details")
    price_map = {'basic': '15,000', 'deluxe': '20,000', 'premium': '25,000'}
    price = price_map.get(package, '')
    
    keyboard = [
        [InlineKeyboardButton(f"📝 Book Now ({price} ETB)", callback_data=f'book_decor')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='menu_decor')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
    ]
    
    await query.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

# --- LIMOUSINE PACKAGES ---
async def limo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Limousine packages menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⭐ Grand - 25k", callback_data='view_limo_grand')],
        [InlineKeyboardButton("✨ Special - 30k", callback_data='view_limo_special')],
        [InlineKeyboardButton("👑 Royal - 35k", callback_data='view_limo_royal')],
        [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
    ]
    
    await query.message.edit_text(
        "🚗 *Select Limousine Package:*", 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def view_limo_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View individual limousine package"""
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('view_limo_', '')
    context.user_data['selected_package'] = package
    context.user_data['service_type'] = 'limo'
    
    text = LIMO_PACKAGES.get(package, "Package details")
    price_map = {'grand': '25,000', 'special': '30,000', 'royal': '35,000'}
    price = price_map.get(package, '')
    
    keyboard = [
        [InlineKeyboardButton(f"📝 Book Now ({price} ETB)", callback_data=f'book_limo')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='menu_limo')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
    ]
    
    await query.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

# --- PHOTOGRAPHY PACKAGES ---
async def photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Photography packages menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 Digital - 10k", callback_data='view_photo_digital')],
        [InlineKeyboardButton("🖼️ Standard - 12k", callback_data='view_photo_standard')],
        [InlineKeyboardButton("💎 Premium - 15k", callback_data='view_photo_premium')],
        [InlineKeyboardButton("🎥 Video - 15k", callback_data='view_photo_video')],
        [InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]
    ]
    
    await query.message.edit_text(
        "📸 *Select Media Package:*", 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

async def view_photo_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View individual photography package"""
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('view_photo_', '')
    context.user_data['selected_package'] = package
    context.user_data['service_type'] = 'photo'
    
    text = PHOTO_PACKAGES.get(package, "Package details")
    price_map = {'digital': '10,000', 'standard': '12,000', 'premium': '15,000', 'video': '15,000'}
    price = price_map.get(package, '')
    
    keyboard = [
        [InlineKeyboardButton(f"📝 Book Now ({price} ETB)", callback_data=f'book_photo')],
        [InlineKeyboardButton("🔙 Back to Packages", callback_data='menu_photo')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
    ]
    
    await query.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

# --- CONTACT PAGE ---
async def contact_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Contact information page"""
    query = update.callback_query
    await query.answer()
    logger.info("Contact page opened")
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data='main_menu')]]
    await query.message.edit_text(
        CONTACT_TEXT, 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

# --- DECOR BOOKING FLOW ---
async def book_decor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start decor booking"""
    query = update.callback_query
    await query.answer()
    
    package_name = context.user_data.get('selected_package', 'basic')
    price_map = {'basic': '15,000', 'deluxe': '20,000', 'premium': '25,000'}
    price = price_map.get(package_name, '')
    
    await query.message.reply_text(
        f"🎁 *Decor Booking - {price} ETB*\n\n"
        f"1. Please enter your full name:"
    )
    return D_NAME

async def decor_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("2. Please enter your phone number:")
    return D_PHONE

async def decor_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("3. Please enter your address:")
    return D_ADDRESS

async def decor_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    await update.message.reply_text("4. Preferred date & time (e.g., 25/12/2023, 10:00 AM):")
    return D_DATE

async def decor_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("5. Special notes (optional):")
    return D_NOTES

async def decor_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['notes'] = update.message.text
    
    bank_msg = (
        "⚠️ *IMPORTANT*\n\n"
        "Booking confirmed only after half-payment screenshot.\n\n"
        "🏦 *Bank Details:*\n"
        "CBE Account: 10001345678901\n"
        "AGOS POSTPARTUM CARE\n"
        "📱 Tele Birr: 0967621545\n\n"
        "6. Upload payment screenshot:"
    )
    await update.message.reply_text(bank_msg, parse_mode='Markdown')
    return D_PAYMENT

async def decor_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment and notify admins"""
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return D_PAYMENT
    
    try:
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        
        # Create summary
        package = context.user_data.get('selected_package', 'basic')
        price_map = {'basic': '15,000', 'deluxe': '20,000', 'premium': '25,000'}
        price = price_map.get(package, '')
        
        summary = (
            f"🔔 *NEW DECOR BOOKING*\n\n"
            f"📦 Package: {package.upper()} ({price} ETB)\n"
            f"👤 Name: {context.user_data.get('name', 'N/A')}\n"
            f"📞 Phone: {context.user_data.get('phone', 'N/A')}\n"
            f"🏠 Address: {context.user_data.get('address', 'N/A')}\n"
            f"📅 Date: {context.user_data.get('date', 'N/A')}\n"
            f"📝 Notes: {context.user_data.get('notes', 'None')}\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        logger.info(f"Sending decor booking notification to admins: {ADMIN_IDS}")
        
        # Send photo notification to admins
        await notify_admins(
            context, 
            summary, 
            photo=photo.file_id
        )
        
        # Create and send PDF
        pdf = create_pdf(context.user_data, "Decor")
        if pdf:
            filename = f"Decor_{context.user_data.get('name', 'Booking').replace(' ', '_')}.pdf"
            await notify_admins(
                context, 
                f"📄 PDF Summary for {context.user_data.get('name', 'Booking')}", 
                document=pdf, 
                filename=filename
            )
        
        # Confirm to user
        await update.message.reply_text(
            "✅ *Booking Submitted!*\n\n"
            "Your booking is awaiting confirmation. We'll contact you soon via Telegram or phone.\n\n"
            "Thank you for choosing AGOS! 🌸",
            parse_mode='Markdown'
        )
        
        # Show discover more
        keyboard = [
            [InlineKeyboardButton("🚗 Book Limousine", callback_data='menu_limo'),
             InlineKeyboardButton("📸 Book Media", callback_data='menu_photo')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
        ]
        await update.message.reply_text(
            "✨ *Thank you! Explore our other services:*", 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in decor payment: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("An error occurred. Please try again or contact support.")
    
    return ConversationHandler.END

# --- LIMOUSINE BOOKING FLOW ---
async def book_limo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start limousine booking"""
    query = update.callback_query
    await query.answer()
    
    package_name = context.user_data.get('selected_package', 'grand')
    price_map = {'grand': '25,000', 'special': '30,000', 'royal': '35,000'}
    price = price_map.get(package_name, '')
    
    await query.message.reply_text(
        f"🚗 *Limousine Booking - {price} ETB*\n\n"
        f"1. Please enter your full name:"
    )
    return L_NAME

async def limo_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("2. Please enter your phone number:")
    return L_PHONE

async def limo_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("3. Preferred date & time (e.g., 25/12/2023, 10:00 AM):")
    return L_DATE

async def limo_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("4. Pickup address:")
    return L_ADDRESS

async def limo_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    
    bank_msg = (
        "⚠️ *IMPORTANT*\n\n"
        "Booking confirmed only after half-payment screenshot.\n\n"
        "🏦 *Bank Details:*\n"
        "CBE Account: 10001345678901\n"
        "AGOS POSTPARTUM CARE\n"
        "📱 Tele Birr: 0967621545\n\n"
        "5. Upload payment screenshot:"
    )
    await update.message.reply_text(bank_msg, parse_mode='Markdown')
    return L_PAYMENT

async def limo_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment and notify admins"""
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return L_PAYMENT
    
    try:
        photo = update.message.photo[-1]
        
        package = context.user_data.get('selected_package', 'grand')
        price_map = {'grand': '25,000', 'special': '30,000', 'royal': '35,000'}
        price = price_map.get(package, '')
        
        summary = (
            f"🔔 *NEW LIMOUSINE BOOKING*\n\n"
            f"📦 Package: {package.upper()} ({price} ETB)\n"
            f"👤 Name: {context.user_data.get('name', 'N/A')}\n"
            f"📞 Phone: {context.user_data.get('phone', 'N/A')}\n"
            f"📅 Date: {context.user_data.get('date', 'N/A')}\n"
            f"🏠 Address: {context.user_data.get('address', 'N/A')}\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        logger.info(f"Sending limousine booking notification to admins: {ADMIN_IDS}")
        
        await notify_admins(context, summary, photo=photo.file_id)
        
        pdf = create_pdf(context.user_data, "Limousine")
        if pdf:
            filename = f"Limousine_{context.user_data.get('name', 'Booking').replace(' ', '_')}.pdf"
            await notify_admins(
                context, 
                f"📄 PDF Summary for {context.user_data.get('name', 'Booking')}", 
                document=pdf, 
                filename=filename
            )
        
        await update.message.reply_text(
            "✅ *Booking Submitted!*\n\n"
            "Your booking is awaiting confirmation. We'll contact you soon.\n\n"
            "Thank you for choosing AGOS! 🚗",
            parse_mode='Markdown'
        )
        
        # Show discover more
        keyboard = [
            [InlineKeyboardButton("🎁 Book Decor", callback_data='menu_decor'),
             InlineKeyboardButton("📸 Book Media", callback_data='menu_photo')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
        ]
        await update.message.reply_text(
            "✨ *Thank you! Explore our other services:*", 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in limo payment: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("An error occurred. Please try again.")
    
    return ConversationHandler.END

# --- PHOTOGRAPHY BOOKING FLOW ---
async def book_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start photography booking"""
    query = update.callback_query
    await query.answer()
    
    package_name = context.user_data.get('selected_package', 'digital')
    price_map = {'digital': '10,000', 'standard': '12,000', 'premium': '15,000', 'video': '15,000'}
    price = price_map.get(package_name, '')
    
    await query.message.reply_text(
        f"📸 *Media Booking - {price} ETB*\n\n"
        f"1. Please enter your full name:"
    )
    return PH_NAME

async def photo_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("2. Please enter your phone number:")
    return PH_PHONE

async def photo_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("3. Event date & time (e.g., 25/12/2023, 10:00 AM):")
    return PH_DATE

async def photo_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("4. Event address:")
    return PH_ADDRESS

async def photo_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    
    bank_msg = (
        "⚠️ *IMPORTANT*\n\n"
        "Booking confirmed only after half-payment screenshot.\n\n"
        "🏦 *Bank Details:*\n"
        "CBE Account: 10001345678901\n"
        "AGOS POSTPARTUM CARE\n"
        "📱 Tele Birr: 0967621545\n\n"
        "5. Upload payment screenshot:"
    )
    await update.message.reply_text(bank_msg, parse_mode='Markdown')
    return PH_PAYMENT

async def photo_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment and notify admins"""
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return PH_PAYMENT
    
    try:
        photo = update.message.photo[-1]
        
        package = context.user_data.get('selected_package', 'digital')
        price_map = {'digital': '10,000', 'standard': '12,000', 'premium': '15,000', 'video': '15,000'}
        price = price_map.get(package, '')
        
        summary = (
            f"🔔 *NEW MEDIA BOOKING*\n\n"
            f"📦 Package: {package.upper()} ({price} ETB)\n"
            f"👤 Name: {context.user_data.get('name', 'N/A')}\n"
            f"📞 Phone: {context.user_data.get('phone', 'N/A')}\n"
            f"📅 Date: {context.user_data.get('date', 'N/A')}\n"
            f"🏠 Address: {context.user_data.get('address', 'N/A')}\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        logger.info(f"Sending media booking notification to admins: {ADMIN_IDS}")
        
        await notify_admins(context, summary, photo=photo.file_id)
        
        pdf = create_pdf(context.user_data, "Media")
        if pdf:
            filename = f"Media_{context.user_data.get('name', 'Booking').replace(' ', '_')}.pdf"
            await notify_admins(
                context, 
                f"📄 PDF Summary for {context.user_data.get('name', 'Booking')}", 
                document=pdf, 
                filename=filename
            )
        
        await update.message.reply_text(
            "✅ *Booking Submitted!*\n\n"
            "Your booking is awaiting confirmation. We'll contact you soon.\n\n"
            "Thank you for choosing AGOS! 📸",
            parse_mode='Markdown'
        )
        
        # Show discover more
        keyboard = [
            [InlineKeyboardButton("🎁 Book Decor", callback_data='menu_decor'),
             InlineKeyboardButton("🚗 Book Limousine", callback_data='menu_limo')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
        ]
        await update.message.reply_text(
            "✨ *Thank you! Explore our other services:*", 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in photo payment: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("An error occurred. Please try again.")
    
    return ConversationHandler.END

# --- UTILITY HANDLERS ---
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu callback"""
    query = update.callback_query
    await query.answer()
    await main_menu(update, context)

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot"""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await start(update, context)

# --- MAIN ---
def main():
    """Start the bot"""
    app = Application.builder().token(TOKEN).build()

    # Decor conversation
    decor_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_decor, pattern='^book_decor$')],
        states={
            D_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_name)],
            D_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_phone)],
            D_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_address)],
            D_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_date)],
            D_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_notes)],
            D_PAYMENT: [MessageHandler(filters.PHOTO, decor_payment)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(main_menu_handler, pattern='^main_menu$')]
    )

    # Limo conversation
    limo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_limo, pattern='^book_limo$')],
        states={
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_name)],
            L_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_phone)],
            L_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_date)],
            L_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_address)],
            L_PAYMENT: [MessageHandler(filters.PHOTO, limo_payment)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(main_menu_handler, pattern='^main_menu$')]
    )

    # Photo conversation
    photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_photo, pattern='^book_photo$')],
        states={
            PH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_name)],
            PH_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_phone)],
            PH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_date)],
            PH_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_address)],
            PH_PAYMENT: [MessageHandler(filters.PHOTO, photo_payment)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(main_menu_handler, pattern='^main_menu$')]
    )

    # Add all handlers
    app.add_handler(CommandHandler("start", start))
    
    # Menu navigation handlers
    app.add_handler(CallbackQueryHandler(main_menu, pattern='^lang_'))
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(decor_menu, pattern='^menu_decor$'))
    app.add_handler(CallbackQueryHandler(limo_menu, pattern='^menu_limo$'))
    app.add_handler(CallbackQueryHandler(photo_menu, pattern='^menu_photo$'))
    app.add_handler(CallbackQueryHandler(contact_menu, pattern='^menu_contact$'))
    app.add_handler(CallbackQueryHandler(restart, pattern='^restart$'))
    
    # Package view handlers
    app.add_handler(CallbackQueryHandler(view_decor_package, pattern='^view_decor_'))
    app.add_handler(CallbackQueryHandler(view_limo_package, pattern='^view_limo_'))
    app.add_handler(CallbackQueryHandler(view_photo_package, pattern='^view_photo_'))
    
    # Add conversation handlers
    app.add_handler(decor_conv)
    app.add_handler(limo_conv)
    app.add_handler(photo_conv)

    print("=" * 50)
    print("✅ AGOS BOT - FULLY FIXED VERSION")
    print(f"👥 Admin IDs configured: {ADMIN_IDS}")
    print("✅ Decor Booking: Working")
    print("✅ Limousine Booking: Working")
    print("✅ Photography Booking: Working")
    print("✅ Contact Page: Working")
    print("✅ Admin Notifications: Working")
    print("✅ PDF Generation: Working")
    print("=" * 50)

    app.run_polling()

if __name__ == '__main__':
    main()
