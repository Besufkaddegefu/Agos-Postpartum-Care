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
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [
    int(os.environ.get("ADMIN_ID_1", "123456789")),
    int(os.environ.get("ADMIN_ID_2", "987654321")),
]
LOGO_PATH = os.environ.get("LOGO_PATH", "logo.webp")

print("=" * 50)
print(f"TOKEN: {TOKEN[:10]}...")
print(f"ADMIN_IDS: {ADMIN_IDS}")
print("=" * 50)

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
            if not key.startswith('_') and value:
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
        return None

# --- NOTIFY ADMINS ---
async def notify_admins(context, message, photo=None, document=None):
    for admin_id in ADMIN_IDS:
        try:
            if photo:
                await context.bot.send_photo(chat_id=admin_id, photo=photo, caption=message[:1024], parse_mode='Markdown')
            elif document:
                await context.bot.send_document(chat_id=admin_id, document=document, filename="booking.pdf", caption=message[:1024])
            else:
                await context.bot.send_message(chat_id=admin_id, text=message, parse_mode='Markdown')
            logger.info(f"Notified admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

# --- START & MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='lang_am')]
    ]
    await update.message.reply_text("🌿 Choose Language:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'lang_en':
        context.user_data['lang'] = 'en'
    elif query.data == 'lang_am':
        context.user_data['lang'] = 'am'
    
    keyboard = [
        [InlineKeyboardButton("🎁 Decor Packages", callback_data='menu_decor'),
         InlineKeyboardButton("🚗 Limousine", callback_data='menu_limo')],
        [InlineKeyboardButton("📸 Media", callback_data='menu_photo'),
         InlineKeyboardButton("📞 Contact", callback_data='menu_contact')],
        [InlineKeyboardButton("🌍 Change Language", callback_data='restart')]
    ]
    
    await query.message.edit_text(WELCOME_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- DECOR PACKAGES ---
async def decor_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔸 Basic - 15k", callback_data='view_decor_basic')],
        [InlineKeyboardButton("💎 Deluxe - 20k", callback_data='view_decor_deluxe')],
        [InlineKeyboardButton("👑 Premium - 25k", callback_data='view_decor_premium')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
    ]
    
    await query.message.edit_text("🎁 *Select Decor Package:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def view_decor_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('view_decor_', '')
    context.user_data['decor_package'] = package
    
    text = DECOR_PACKAGES.get(package, "Package details")
    keyboard = [
        [InlineKeyboardButton("📝 Book Now", callback_data=f'book_decor_{package}')],
        [InlineKeyboardButton("🔙 Back", callback_data='menu_decor')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- DECOR BOOKING FLOW ---
async def book_decor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('book_decor_', '')
    context.user_data['booking_type'] = 'decor'
    context.user_data['package'] = package
    
    await query.message.reply_text("📝 *Decor Booking*\n\n1. Please enter your full name:")
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
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return D_PAYMENT
    
    photo = update.message.photo[-1]
    
    # Create summary
    summary = (
        f"🔔 *NEW DECOR BOOKING*\n\n"
        f"📦 Package: {context.user_data.get('package')}\n"
        f"👤 Name: {context.user_data.get('name')}\n"
        f"📞 Phone: {context.user_data.get('phone')}\n"
        f"🏠 Address: {context.user_data.get('address')}\n"
        f"📅 Date: {context.user_data.get('date')}\n"
        f"📝 Notes: {context.user_data.get('notes', 'None')}"
    )
    
    # Create PDF
    pdf = create_pdf(context.user_data, "Decor")
    
    # Notify admins
    await notify_admins(context, summary, photo=photo.file_id)
    if pdf:
        await notify_admins(context, "📄 Booking PDF:", document=pdf)
    
    # Confirm to user
    await update.message.reply_text("✅ Booking submitted! Awaiting confirmation.")
    
    # Show discover more
    keyboard = [
        [InlineKeyboardButton("🚗 Book Limousine", callback_data='menu_limo'),
         InlineKeyboardButton("📸 Book Media", callback_data='menu_photo')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
    ]
    await update.message.reply_text("✨ *Thank you!* Explore our other services:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    return ConversationHandler.END

# --- LIMOUSINE BOOKING FLOW ---
async def limo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⭐ Grand - 25k", callback_data='view_limo_grand')],
        [InlineKeyboardButton("✨ Special - 30k", callback_data='view_limo_special')],
        [InlineKeyboardButton("👑 Royal - 35k", callback_data='view_limo_royal')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
    ]
    
    await query.message.edit_text("🚗 *Select Limousine Package:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def view_limo_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('view_limo_', '')
    context.user_data['limo_package'] = package
    
    text = LIMO_PACKAGES.get(package, "Package details")
    keyboard = [
        [InlineKeyboardButton("📝 Book Now", callback_data=f'book_limo_{package}')],
        [InlineKeyboardButton("🔙 Back", callback_data='menu_limo')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def book_limo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('book_limo_', '')
    context.user_data['booking_type'] = 'limo'
    context.user_data['package'] = package
    
    await query.message.reply_text("🚗 *Limousine Booking*\n\n1. Please enter your full name:")
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
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return L_PAYMENT
    
    photo = update.message.photo[-1]
    
    summary = (
        f"🔔 *NEW LIMOUSINE BOOKING*\n\n"
        f"📦 Package: {context.user_data.get('package')}\n"
        f"👤 Name: {context.user_data.get('name')}\n"
        f"📞 Phone: {context.user_data.get('phone')}\n"
        f"📅 Date: {context.user_data.get('date')}\n"
        f"🏠 Address: {context.user_data.get('address')}"
    )
    
    pdf = create_pdf(context.user_data, "Limousine")
    
    await notify_admins(context, summary, photo=photo.file_id)
    if pdf:
        await notify_admins(context, "📄 Booking PDF:", document=pdf)
    
    await update.message.reply_text("✅ Booking submitted! Awaiting confirmation.")
    
    # Show discover more
    keyboard = [
        [InlineKeyboardButton("🎁 Book Decor", callback_data='menu_decor'),
         InlineKeyboardButton("📸 Book Media", callback_data='menu_photo')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
    ]
    await update.message.reply_text("✨ *Thank you!* Explore our other services:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    return ConversationHandler.END

# --- PHOTOGRAPHY BOOKING FLOW ---
async def photo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 Digital - 10k", callback_data='view_photo_digital')],
        [InlineKeyboardButton("🖼️ Standard - 12k", callback_data='view_photo_standard')],
        [InlineKeyboardButton("💎 Premium - 15k", callback_data='view_photo_premium')],
        [InlineKeyboardButton("🎥 Video - 15k", callback_data='view_photo_video')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
    ]
    
    await query.message.edit_text("📸 *Select Media Package:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def view_photo_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('view_photo_', '')
    context.user_data['photo_package'] = package
    
    text = PHOTO_PACKAGES.get(package, "Package details")
    keyboard = [
        [InlineKeyboardButton("📝 Book Now", callback_data=f'book_photo_{package}')],
        [InlineKeyboardButton("🔙 Back", callback_data='menu_photo')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def book_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = query.data.replace('book_photo_', '')
    context.user_data['booking_type'] = 'photo'
    context.user_data['package'] = package
    
    await query.message.reply_text("📸 *Media Booking*\n\n1. Please enter your full name:")
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
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return PH_PAYMENT
    
    photo = update.message.photo[-1]
    
    summary = (
        f"🔔 *NEW MEDIA BOOKING*\n\n"
        f"📦 Package: {context.user_data.get('package')}\n"
        f"👤 Name: {context.user_data.get('name')}\n"
        f"📞 Phone: {context.user_data.get('phone')}\n"
        f"📅 Date: {context.user_data.get('date')}\n"
        f"🏠 Address: {context.user_data.get('address')}"
    )
    
    pdf = create_pdf(context.user_data, "Media")
    
    await notify_admins(context, summary, photo=photo.file_id)
    if pdf:
        await notify_admins(context, "📄 Booking PDF:", document=pdf)
    
    await update.message.reply_text("✅ Booking submitted! Awaiting confirmation.")
    
    # Show discover more
    keyboard = [
        [InlineKeyboardButton("🎁 Book Decor", callback_data='menu_decor'),
         InlineKeyboardButton("🚗 Book Limousine", callback_data='menu_limo')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='back_to_main')]
    ]
    await update.message.reply_text("✨ *Thank you!* Explore our other services:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    return ConversationHandler.END

# --- CONTACT & UTILITIES ---
async def contact_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
    await query.message.edit_text(CONTACT_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await main_menu(update, context)

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await start(update, context)

# --- MAIN ---
def main():
    app = Application.builder().token(TOKEN).build()

    # Decor conversation
    decor_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_decor, pattern='^book_decor_')],
        states={
            D_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_name)],
            D_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_phone)],
            D_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_address)],
            D_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_date)],
            D_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_notes)],
            D_PAYMENT: [MessageHandler(filters.PHOTO, decor_payment)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(back_to_main, pattern='back_to_main')]
    )

    # Limo conversation
    limo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_limo, pattern='^book_limo_')],
        states={
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_name)],
            L_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_phone)],
            L_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_date)],
            L_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, limo_address)],
            L_PAYMENT: [MessageHandler(filters.PHOTO, limo_payment)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(back_to_main, pattern='back_to_main')]
    )

    # Photo conversation
    photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(book_photo, pattern='^book_photo_')],
        states={
            PH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_name)],
            PH_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_phone)],
            PH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_date)],
            PH_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_address)],
            PH_PAYMENT: [MessageHandler(filters.PHOTO, photo_payment)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(back_to_main, pattern='back_to_main')]
    )

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(main_menu, pattern='^lang_'))
    app.add_handler(CallbackQueryHandler(main_menu, pattern='^back_to_main$'))
    app.add_handler(CallbackQueryHandler(decor_menu, pattern='^menu_decor$'))
    app.add_handler(CallbackQueryHandler(limo_menu, pattern='^menu_limo$'))
    app.add_handler(CallbackQueryHandler(photo_menu, pattern='^menu_photo$'))
    app.add_handler(CallbackQueryHandler(contact_menu, pattern='^menu_contact$'))
    app.add_handler(CallbackQueryHandler(restart, pattern='^restart$'))
    
    # Package view handlers
    app.add_handler(CallbackQueryHandler(view_decor_package, pattern='^view_decor_'))
    app.add_handler(CallbackQueryHandler(view_limo_package, pattern='^view_limo_'))
    app.add_handler(CallbackQueryHandler(view_photo_package, pattern='^view_photo_'))
    
    # Add conversations
    app.add_handler(decor_conv)
    app.add_handler(limo_conv)
    app.add_handler(photo_conv)

    print("=" * 50)
    print("✅ AGOS Bot - SIMPLIFIED VERSION")
    print(f"👥 Admin IDs: {ADMIN_IDS}")
    print("✅ Decor Booking: 6 steps")
    print("✅ Limousine Booking: 5 steps")
    print("✅ Photography Booking: 5 steps")
    print("✅ Contact page: Working")
    print("✅ Admin notifications: Working")
    print("=" * 50)

    app.run_polling()

if __name__ == '__main__':
    main()
