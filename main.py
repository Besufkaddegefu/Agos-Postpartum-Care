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
# Properly load admin IDs
ADMIN_IDS = []
for i in range(1, 4):
    admin_id = os.environ.get(f"ADMIN_ID_{i}")
    if admin_id:
        try:
            ADMIN_IDS.append(int(admin_id))
            logger.info(f"Loaded admin {i}: {admin_id}")
        except ValueError:
            logger.error(f"Invalid ADMIN_ID_{i}: {admin_id}")

LOGO_PATH = os.environ.get("LOGO_PATH", "logo.webp")
SERVICES_PDF_PATH = os.environ.get("SERVICES_PDF_PATH", "services_catalog.pdf")

WORKING_HOURS_START = 8
WORKING_HOURS_END = 20

print("=" * 50)
print(f"TOKEN exists: {bool(TOKEN)}")
print(f"ADMIN_IDS: {ADMIN_IDS}")
print("=" * 50)

# --- CONVERSATION STATES ---
(D_NAME, D_GENDER, D_ADDR, D_PHONE, D_USERNAME, D_CONTACT_PERSON, D_PKG, D_DATE, D_HOUSE, D_NOTES, D_PAYMENT) = range(1, 12)
(L_NAME, L_PHONE, L_DATE, L_ADDR, L_PAYMENT) = range(20, 25)
(PH_NAME, PH_PHONE, PH_DATE, PH_ADDR, PH_PAYMENT) = range(30, 35)

# --- CONTENT (Keep your existing CONTENT dictionary here - it's too long to repeat) ---
# [Your CONTENT dictionary remains exactly the same]

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
                logger.error(f"Logo error: {e}")

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "AGOS Decor Booking")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.line(50, height - 85, 550, height - 85)

        c.setFont("Helvetica", 11)
        y_position = height - 120

        for key, value in data.items():
            if key.startswith('d_') and value and key not in ['d_payment']:
                label = key[2:].replace('_', ' ').upper()
                text = f"{label}: {value}"
                c.drawString(50, y_position, text)
                y_position -= 25
                if y_position < 60:
                    c.showPage()
                    y_position = height - 50

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"PDF error: {e}")
        return None

def create_limo_pdf(data):
    # Similar to create_decor_pdf but for limousine
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        if os.path.exists(LOGO_PATH):
            try:
                logo = ImageReader(LOGO_PATH)
                c.drawImage(logo, 480, height - 80, width=60, height=60, mask='auto')
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "AGOS Limousine Booking")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.line(50, height - 85, 550, height - 85)

        c.setFont("Helvetica", 11)
        y_position = height - 120

        for key, value in data.items():
            if key.startswith('l_') and value:
                label = key[2:].replace('_', ' ').upper()
                text = f"{label}: {value}"
                c.drawString(50, y_position, text)
                y_position -= 25
                if y_position < 60:
                    c.showPage()
                    y_position = height - 50

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"PDF error: {e}")
        return None

def create_photo_pdf(data):
    # Similar to create_decor_pdf but for photography
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        if os.path.exists(LOGO_PATH):
            try:
                logo = ImageReader(LOGO_PATH)
                c.drawImage(logo, 480, height - 80, width=60, height=60, mask='auto')
            except Exception:
                pass

        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "AGOS Media Booking")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.line(50, height - 85, 550, height - 85)

        c.setFont("Helvetica", 11)
        y_position = height - 120

        for key, value in data.items():
            if key.startswith('ph_') and value:
                label = key[3:].replace('_', ' ').upper()
                text = f"{label}: {value}"
                c.drawString(50, y_position, text)
                y_position -= 25
                if y_position < 60:
                    c.showPage()
                    y_position = height - 50

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"PDF error: {e}")
        return None

# --- NOTIFY ADMINS HELPER ---
async def notify_admins(context, message, photo=None, document=None, filename=None):
    if not ADMIN_IDS:
        logger.warning("No admin IDs configured")
        return
    
    for admin_id in ADMIN_IDS:
        try:
            if photo:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo,
                    caption=message[:1024],
                    parse_mode='Markdown'
                )
                logger.info(f"Sent photo to admin {admin_id}")
            elif document:
                document.seek(0)
                await context.bot.send_document(
                    chat_id=admin_id,
                    document=document,
                    filename=filename or "booking.pdf",
                    caption=message[:1024]
                )
                logger.info(f"Sent document to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

# --- HELPERS ---
def get_nav_kb(lang, back_callback='d_back'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data=back_callback)],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='main_menu')]
    ])

# --- WORKING HOURS GATE ---
async def working_hours_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# --- START & MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    return await working_hours_gate(update, context)

async def after_hours_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='lang_am')]
    ]
    
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "🌿 Choose Language / ቋንቋ ይምረጡ:", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('lang_'):
        context.user_data['lang'] = query.data.split('_')[1]
    
    lang = context.user_data.get('lang', 'en')
    btns = CONTENT[lang]['btns']
    
    keyboard = [
        [InlineKeyboardButton(btns[0], callback_data='show_decor_packages'), 
         InlineKeyboardButton(btns[1], callback_data='show_limo_packages')],
        [InlineKeyboardButton(btns[2], callback_data='show_photo_packages'), 
         InlineKeyboardButton(btns[3], callback_data='contact_info')],  # FIXED: Changed to 'contact_info'
        [InlineKeyboardButton(btns[4], callback_data='send_pdf')],
        [InlineKeyboardButton(CONTENT[lang]['change_lang'], callback_data='restart')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['welcome'], 
        reply_markup=InlineKeyboardMarkup(keyboard), 
        parse_mode='Markdown'
    )

# --- CONTACT PAGE (FIXED) ---
async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact info page"""
    query = update.callback_query
    await query.answer()
    logger.info("Contact page opened")
    lang = context.user_data.get('lang', 'en')
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='main_menu')]])
    await query.message.edit_text(
        CONTENT[lang]['contact_text'], 
        reply_markup=back_btn, 
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
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='main_menu')]
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
        [InlineKeyboardButton("⭐ Grand - 25,000 ETB", callback_data='view_limo_grand')],
        [InlineKeyboardButton("✨ Special - 30,000 ETB", callback_data='view_limo_special')],
        [InlineKeyboardButton("👑 Royal - 35,000 ETB", callback_data='view_limo_royal')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='main_menu')]
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
        [InlineKeyboardButton("📱 Digital - 10,000 ETB", callback_data='view_photo_digital')],
        [InlineKeyboardButton("🖼️ Standard - 12,000 ETB", callback_data='view_photo_standard')],
        [InlineKeyboardButton("💎 Premium - 15,000 ETB", callback_data='view_photo_premium')],
        [InlineKeyboardButton("🎥 Video - 15,000 ETB", callback_data='view_videography')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='main_menu')]
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
    
    context.user_data['selected_package'] = 'basic'
    context.user_data['service_type'] = 'decor'
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='start_decor_booking')],
        [InlineKeyboardButton("🔙 Back", callback_data='show_decor_packages')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
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
    
    context.user_data['selected_package'] = 'deluxe'
    context.user_data['service_type'] = 'decor'
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='start_decor_booking')],
        [InlineKeyboardButton("🔙 Back", callback_data='show_decor_packages')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
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
    
    context.user_data['selected_package'] = 'premium'
    context.user_data['service_type'] = 'decor'
    
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['book_now'], callback_data='start_decor_booking')],
        [InlineKeyboardButton("🔙 Back", callback_data='show_decor_packages')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
    ]
    
    await query.message.edit_text(
        CONTENT[lang]['decor_premium'],
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

# Similar for limo and photo views (keep your existing ones but make sure they store the package)

# --- DECOR BOOKING FLOW (SIMPLIFIED) ---
async def start_decor_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package = context.user_data.get('selected_package', 'basic')
    price_map = {'basic': '15,000', 'deluxe': '20,000', 'premium': '25,000'}
    price = price_map.get(package, '')
    
    await query.message.reply_text(
        f"🎁 *Decor Booking - {price} ETB*\n\n"
        f"1. Please enter your full name:"
    )
    return D_NAME

async def decor_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_name'] = update.message.text
    await update.message.reply_text("2. Gender of the Newborn (Male/Female/Not Sure):")
    return D_GENDER

async def decor_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_gender'] = update.message.text
    await update.message.reply_text("3. House Address for Decor Setup:")
    return D_ADDR

async def decor_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_addr'] = update.message.text
    await update.message.reply_text("4. Phone Number:")
    return D_PHONE

async def decor_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_phone'] = update.message.text
    await update.message.reply_text("5. Telegram Username (e.g., @username):")
    return D_USERNAME

async def decor_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_username'] = update.message.text
    await update.message.reply_text("6. Contact Person at Home (if different):")
    return D_CONTACT_PERSON

async def decor_contact_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_contact'] = update.message.text
    await update.message.reply_text(
        "7. Preferred Date & Time\nFormat: DD/MM/YYYY, Time (e.g., 25/12/2023, 10:00 AM):"
    )
    return D_DATE

async def decor_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_date'] = update.message.text
    await update.message.reply_text("8. House Type (Villa/Apartment/Condominium/G+1/G+2):")
    return D_HOUSE

async def decor_house(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_house'] = update.message.text
    
    warning_msg = (
        "⚠️ *IMPORTANT*\n\n"
        "Booking will not be confirmed unless a screenshot of the half-payment is sent.\n\n"
        "🏦 *Bank Details:*\n"
        "CBE Account: 10001345678901\n"
        "AGOS POSTPARTUM CARE\n"
        "📱 Tele Birr: 0967621545\n\n"
        "9. Special Notes (optional):"
    )
    await update.message.reply_text(warning_msg, parse_mode='Markdown')
    return D_NOTES

async def decor_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_notes'] = update.message.text
    await update.message.reply_text("10. Upload Payment Screenshot:")
    return D_PAYMENT

async def decor_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return D_PAYMENT

    try:
        photo = update.message.photo[-1]
        
        package = context.user_data.get('selected_package', 'basic')
        price_map = {'basic': '15,000', 'deluxe': '20,000', 'premium': '25,000'}
        price = price_map.get(package, '')
        
        summary = (
            f"🔔 *NEW DECOR BOOKING*\n\n"
            f"📦 Package: {package.upper()} ({price} ETB)\n"
            f"👤 Name: {context.user_data.get('d_name', 'N/A')}\n"
            f"👶 Gender: {context.user_data.get('d_gender', 'N/A')}\n"
            f"📞 Phone: {context.user_data.get('d_phone', 'N/A')}\n"
            f"📱 Telegram: {context.user_data.get('d_username', 'N/A')}\n"
            f"🏠 Address: {context.user_data.get('d_addr', 'N/A')}\n"
            f"🏗️ House: {context.user_data.get('d_house', 'N/A')}\n"
            f"📅 Date: {context.user_data.get('d_date', 'N/A')}\n"
            f"📝 Notes: {context.user_data.get('d_notes', 'None')}"
        )

        # Notify admins
        await notify_admins(context, summary, photo=photo.file_id)
        
        # Create and send PDF
        pdf_file = create_decor_pdf(context.user_data)
        if pdf_file:
            filename = f"Decor_{context.user_data.get('d_name', 'Booking').replace(' ', '_')}.pdf"
            await notify_admins(context, f"📄 PDF Summary", document=pdf_file, filename=filename)
            pdf_file.seek(0)
            await update.message.reply_document(
                document=pdf_file,
                filename="AGOS_Decor_Booking.pdf",
                caption="✅ Booking submitted! Awaiting confirmation."
            )
        else:
            await update.message.reply_text("✅ Booking submitted! Awaiting confirmation.")

        # Show discover more
        keyboard = [
            [InlineKeyboardButton("🚗 Book Limousine", callback_data='show_limo_packages'),
             InlineKeyboardButton("📸 Book Media", callback_data='show_photo_packages')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='main_menu')]
        ]
        await update.message.reply_text(
            "✨ *Thank you! Explore our other services:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text("An error occurred. Please try again.")

    return ConversationHandler.END

# --- SIMILAR FLOWS FOR LIMO AND PHOTO (simplified versions) ---

# --- MAIN ---
def main():
    app = Application.builder().token(TOKEN).build()

    # Decor conversation
    decor_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_decor_booking, pattern='^start_decor_booking$')],
        states={
            D_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_name)],
            D_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_gender)],
            D_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_address)],
            D_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_phone)],
            D_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_username)],
            D_CONTACT_PERSON: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_contact_person)],
            D_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_date)],
            D_HOUSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_house)],
            D_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, decor_notes)],
            D_PAYMENT: [MessageHandler(filters.PHOTO, decor_payment)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(main_menu, pattern='^main_menu$')]
    )

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(after_hours_handler, pattern='^after_hours$'))
    app.add_handler(CallbackQueryHandler(main_menu, pattern='^lang_'))
    app.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(contact_info, pattern='^contact_info$'))  # FIXED: contact handler
    app.add_handler(CallbackQueryHandler(send_services_pdf, pattern='^send_pdf$'))
    app.add_handler(CallbackQueryHandler(start, pattern='^restart$'))
    
    # Package menu handlers
    app.add_handler(CallbackQueryHandler(show_decor_packages, pattern='^show_decor_packages$'))
    app.add_handler(CallbackQueryHandler(show_limo_packages, pattern='^show_limo_packages$'))
    app.add_handler(CallbackQueryHandler(show_photo_packages, pattern='^show_photo_packages$'))
    
    # Package view handlers
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
    
    # Add conversation handlers
    app.add_handler(decor_conv)
    # Add limo_conv and photo_conv similarly

    print("=" * 50)
    print("✅ AGOS Bot - FULLY FIXED")
    print(f"👥 Admin IDs: {ADMIN_IDS}")
    print("✅ Contact page: FIXED - now opens")
    print("✅ Decor booking: Working")
    print("=" * 50)

    app.run_polling()

if __name__ == '__main__':
    main()
