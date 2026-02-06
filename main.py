import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardRemove)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes, ConversationHandler)

# --- CONFIGURATION ---
TOKEN = "8294060672:AAGKS15my2tj3MMeSB4-nxAf31KoRm9YCbU"
ADMIN_ID = 8057255966
LOGO_PATH = "logo.w"  # Ensure your logo file is named this and in the same folder

# --- CONVERSATION STATES ---
(P_TERMS, P_NAME, P_ADDR, P_AGE, P_PHONE, P_EDD, P_W_BEFORE, P_W_NOW,
 P_BIRTH, P_GENDER, P_DIET, P_RISK, P_ALLERGY, P_BREASTFEED, P_LANG_PREF, P_NOTES,
 P_HOME, P_PACKAGE, P_ID) = range(10, 29)

(D_NAME, D_GENDER, D_ADDR, D_PHONE, D_CONTACT, D_PKG, D_DATE, D_HOUSE, D_PAYMENT, D_NOTES) = range(40, 50)

# --- CONTENT ---
CONTENT = {
    'en': {
        'welcome': "🌿 *Welcome to Agos Postpartum Care* 🌸\n\n_Nurturing mothers, empowering families._",
        'btns': ["👩‍🍼 Postpartum Care", "🎁 Decor", "🚗 Arrival", "📸 Media", "📞 Contact", "📋 Postpartum Care Booking", "📅 Decor Booking"],
        'care_text': (
            "👩‍🍼 *Postpartum Care Packages*\n"
            "__________________________\n\n"
            "🌟 **Full Postpartum Care (40 Days) — 95,000 ETB**\n\n"
            "• Welcome surprise décor\n\n"
            "• Certified Nutritionist\n\n"
            "• Certified Nanny\n\n"
            "• Personal Chef\n\n"
            "• Professional Massager\n\n"
            "• Nurse\n\n"
            "__________________________\n\n"
            "🌙 **Half Postpartum Care (30 Days) — 85,000 ETB**\n\n"
            "• Welcome surprise décor\n\n"
            "• Certified Nutritionist\n\n"
            "• Certified Nanny\n\n"
            "• Personal Chef\n\n"
            "• Professional Massager\n\n"
            "• Nurse\n\n"
            "__________________________\n\n"
            "💎 **Full Premium Care (40 Days) — 85,000 ETB**\n\n"
            "• Certified Nutritionist\n\n"
            "• Certified Nanny\n\n"
            "• Personal Chef\n\n"
            "• Professional Massager\n\n"
            "• Nurse\n\n"
            "__________________________\n\n"
            "✨ **Half Premium Care (30 Days) — 75,000 ETB**\n\n"
            "• Certified Nutritionist\n\n"
            "• Certified Nanny\n\n"
            "• Personal Chef\n\n"
            "• Professional Massager\n\n"
            "• Nurse\n\n"
            "__________________________\n\n"
            "✅ **Full Standard Care (40 Days) — 75,000 ETB**\n\n"
            "• Certified Nutritionist\n\n"
            "• Personal Chef\n\n"
            "• Professional Massager\n\n"
            "• Nurse\n\n"
            "__________________________\n\n"
            "🔸 **Half Standard Care (30 Days) — 65,000 ETB**\n\n"
            "• Certified Nutritionist\n\n"
            "• Personal Chef\n\n"
            "• Professional Massager\n\n"
            "• Nurse\n\n"
            "__________________________\n\n"
            "🏠 **Full Basic Care (40 Days) — 55,000 ETB**\n\n"
            "• Certified Nutritionist\n\n"
            "• Professional Massager\n\n"
            "• Nurse\n\n"
            "__________________________\n\n"
            "🌿 **Half Basic Care (30 Days) — 45,000 ETB**\n\n"
            "• Certified Nutritionist\n\n"
            "• Professional Massager\n\n"
            "• Nurse"
        ),

        'decor_text': (
            "🎁 *Home Decor Packages*\n"
            "__________________________\n\n"
            "🔸 **Home Decor (15,000 ETB)**\n\n"
            "• Bedroom Decoration\n\n"
            "• Floor Decoration\n\n"
            "• Corridor Decoration\n\n"
            "• Salon Decoration\n\n"
            "__________________________\n\n"
            "💎 **Home Decor Deluxe (20,000 ETB)**\n\n"
            "• Bedroom, Corridor & Salon Decor\n\n"
            "• Large Flower Arrangement (Bouquet + Floor)\n\n"
            "• 2 Kg Normal Cake\n\n"
            "__________________________\n\n"
            "👑 **Home Decor Premium (25,000 ETB)**\n\n"
            "• Bedroom Decor with Agober rent (2 weeks)\n\n"
            "• Corridor & Salon Decor\n\n"
            "• Large Flower Arrangement (Bouquet + Floor)\n\n"
            "• 2 Kg Custom Made Cake"
        ),

        'arrival_text': (
            "🚗 *The Grand Arrival*\n"
            "__________________________\n\n"
            "⭐ **The Grand Arrival (25,000 ETB)**\n\n"
            "• Special limousine service\n\n"
            "• Grand and elegant ride home\n\n"
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
            "📸 *Media Coverage*\n"
            "__________________________\n\n"
            "📱 **Digital Photography (10,000 ETB)**\n\n"
            "• Professional photography\n\n"
            "• All photos delivered in soft copy\n\n"
            "• (No physical album)\n\n"
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
            "📱 +251 967 621 545\n"
            "📱 +251 980 040 468\n\n"
            "🎵 **Follow us on TikTok:**\n"
            "[Agos Postpartum TikTok](https://www.tiktok.com/@agos_postpartumcare)\n\n"
            "🌐 [www.agospostpartumcare.com](https://www.agospostpartumcare.com/)\n"
            "📍 Piassa, Abat Commercial"
        ),
        'agree_btn': "I Agree ✅",
        'back': "🔙 Back to Menu",
        'change_lang': "🌍 Change Language / ቋንቋ ቀይር",
        'q_back': "⬅️ Previous Question"
    },
    'am': {
        'welcome': "🌿 *እንኳን ወደ አጎስ የድህረ ወሊድ እንክብካቤ በሰላም መጡ* 🌸",
        'btns': ["👩‍🍼 የድህረ ወሊድ እንክብካቤ", "🎁 ዲኮር", "🚗 ሊሙዚን", "📸 ፎቶ/ቪዲዮ", "📞 ያግኙን", "📋 የድህረ ወሊድ እንክብካቤ ምዝገባ", "📅 ዲኮር ይዘዙ"],
        'care_text': (
            "👩‍🍼 *የድህረ ወሊድ እንክብካቤ ፓኬጆች*\n"
            "__________________________\n\n"
            "🌟 **ሙሉ የድህረ ወሊድ እንክብካቤ (40 ቀን) — 95,000 ብር**\n\n"
            "• የሰርፕራይዝ ዲኮር\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• የተረጋገጠላት ሞግዚት\n\n"
            "• የግል ሼፍ (ምግብ አብሳይ)\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ\n\n"
            "__________________________\n\n"
            "🌙 **ግማሽ የድህረ ወሊድ እንክብካቤ (30 ቀን) — 85,000 ብር**\n\n"
            "• የሰርፕራይዝ ዲኮር\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• የተረጋገጠላት ሞግዚት\n\n"
            "• የግል ሼፍ\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ\n\n"
            "__________________________\n\n"
            "💎 **ሙሉ ፕሪሚየም እንክብካቤ (40 ቀን) — 85,000 ብር**\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• የተረጋገጠላት ሞግዚት\n\n"
            "• የግል ሼፍ\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ\n\n"
            "__________________________\n\n"
            "✨ **ግማሽ ፕሪሚየም እንክብካቤ (30 ቀን) — 75,000 ብር**\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• የተረጋገጠላት ሞግዚት\n\n"
            "• የግል ሼፍ\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ\n\n"
            "__________________________\n\n"
            "✅ **ሙሉ መደበኛ እንክብካቤ (40 ቀን) — 75,000 ብር**\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• የግል ሼፍ\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ\n\n"
            "__________________________\n\n"
            "🔸 **ግማሽ መደበኛ እንክብካቤ (30 ቀን) — 65,000 ብር**\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• የግል ሼፍ\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ\n\n"
            "__________________________\n\n"
            "🏠 **ሙሉ መሰረታዊ እንክብካቤ (40 ቀን) — 55,000 ብር**\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ\n\n"
            "__________________________\n\n"
            "🌿 **ግማሽ መሰረታዊ እንክብካቤ (30 ቀን) — 45,000 ብር**\n\n"
            "• ስነ-ምግብ ባለሙያ\n\n"
            "• ፕሮፌሽናል ማሳጅ\n\n"
            "• ነርስ"
        ),

        'decor_text': (
            "🎁 *የዲኮር ፓኬጆች*\n"
            "__________________________\n\n"
            "🔸 **መደበኛ ዲኮር (15,000 ብር)**\n\n"
            "• የመኝታ ቤት ዲኮር\n\n"
            "• የወለል ዲኮር\n\n"
            "• የኮሪደር ዲኮር\n\n"
            "• የሳሎን ዲኮር\n\n"
            "__________________________\n\n"
            "💎 **ደልክስ ዲኮር (20,000 ብር)**\n\n"
            "• የመኝታ ቤት፣ ኮሪደር እና ሳሎን ዲኮር\n\n"
            "• ትልቅ የአበባ ዝግጅት (Bouquet + Floor) \n\n"
            "• 2 ኪሎ መደበኛ ኬክ\n\n"
            "__________________________\n\n"
            "👑 **ፕሪሚየም ዲኮር (25,000 ብር)**\n\n"
            "• የመኝታ ቤት ዲኮር ከአጎበር ኪራይ ጋር (2 ሳምንት)\n\n"
            "• የኮሪደር እና ሳሎን ዲኮር\n\n"
            "• ትልቅ የአበባ ዝግጅት (Bouquet + Floor) \n\n"
            "• 2 ኪሎ ተለይቶ የታዘዘ (Custom) ኬክ"
        ),

        'arrival_text': (
            "🚗 *የሊሙዚን አገልግሎት*\n"
            "__________________________\n\n"
            "⭐ **መደበኛ አቀባበል (25,000 ብር)**\n\n"
            "• ለአዲሷ እናት የተዘጋጀ ልዩ የሊሙዚን አገልግሎት\n\n"
            "• ወደ ቤት የሚደረገውን ጉዞ በታላቅ እና ውብ በሆነ አቀባበል የማይረሳ ያድርጉት።\n\n"
            "__________________________\n\n"
            "✨ **ልዩ አቀባበል (30,000 ብር)**\n\n"
            "• ልዩ የሊሙዚን አገልግሎት\n\n"
            "• የቅንጦት እና ልብ የሚነካ የቤት ጉዞ በማድረግ የማይረሳ ትዝታን ይፍጠሩ።\n\n"
            "__________________________\n\n"
            "👑 **የሮያል አቀባበል (35,000 ብር)**\n\n"
            "• የማይረሳ የቤት መመለሻ ትውስታ\n\n"
            "• በልዩ የሊሙዚን አገልግሎት ንግስታዊ በሆነ አቀባበል ወደ ቤትዎ ይግቡ።"
        ),

        'media_text': (
            "📸 *ፎቶ እና ቪዲዮ*\n"
            "__________________________\n\n"
            "📱 **ዲጂታል ፎቶግራፍ (10,000 ብር)**\n\n"
            "• የባለሙያ ፎቶግራፍ አገልግሎት\n\n"
            "• ሁሉም ፎቶዎች በሶፍት ኮፒ (በዲጂታል) የሚሰጡ\n\n"
            "• (አልበም የሌለው)\n\n"
            "__________________________\n\n"
            "🖼️ **መደበኛ ፎቶግራፍ (12,000 ብር)**\n\n"
            "• 100 የታተሙ ፎቶዎች ከመደበኛ አልበም ጋር\n\n"
            "• የሁሉም ፎቶዎች ሶፍት ኮፒን ያካትታል\n\n"
            "__________________________\n\n"
            "💎 **ፕሪሚየም ፎቶግራፍ (15,000 ብር)**\n\n"
            "• ላሚኔት የተደረገ ጥራት ያለው አልበም (20x30 ሴ.ሜ)\n\n"
            "• የሁሉም ፎቶዎች ሶፍት ኮፒን ያካትታል\n\n"
            "__________________________\n\n"
            "🎥 **የቪዲዮ አገልግሎት (15,000 ብር)**\n\n"
            "• ሙሉ የቪዲዮ ሽፋን እና ኤዲቲንግ\n\n"
            "• ሙሉ የቪዲዮ ቀረጻ ሽፋን\n\n"
            "• በባለሙያ ኤዲት የተደረገ ቪዲዮ (Soft Copy)"
        ),

        'contact_text': (
            "📞 *ያግኙን*\n\n"
            "📱 +251 967 621 545\n"
            "📱 +251 980 040 468\n\n"
            "🎵 **በቲኩቶክ ይከተሉን:**\n"
            "[አጎስ በቲኩቶክ](https://www.tiktok.com/@agos_postpartumcare)\n\n"
            "🌐 [www.agospostpartumcare.com](https://www.agospostpartumcare.com/)\n"
            "📍 ፒያሳ፣ አባት ኮሜርሻል"
        ),
        'agree_btn': "እስማማለሁ ✅",
        'back': "🔙 ወደ ዋና ማውጫ",
        'change_lang': "🌍 Change Language / ቋንቋ ቀይር",
        'q_back': "⬅️ ወደ ኋላ ተመለስ"
    }
}

# --- FULL AMHARIC TERMS ---
TERMS_AM = """📋 **የአገልግሎት ውል ስምምነት**
ይህውል ከዚህ በኋላ “ውል ሰጪ” ተብሎ በሚጠራው አጎስ ድህረ ወሊድ እንክብካቤ አዴራሻ፡- አዲስ አበባ, ኢትዮጵያ, ክ/ከተማ: አራዳ, ወረዳ: 02, የቤት ቁጥር: 613, ስልክ ቁጥር: 0967621545, ከዚህ በኋላ ይህን በ “ውል ሰጪ” ተብሎ ይጠራል።

እና ከዚህ በኋላ “ውል ተቀባይ” ተብሎ በሚጠራው-----------------አድራሻ፡- አ.አ. ከተማ-----------ክ/ከተማ ስልክ ቁጥር ---------መካከለው የደህንነት እንክብካቤ አገልግሎት ለማግኘት የተደረገ የአገልግሎት ውል ስምምነት ነው።

አንቀጽ አንድ፡ ስለ ውል ይዘት
አገልግሎት ሰጪ የድህረ ወሊድ እንክብካቤ አገልግሎት ሰጪ ተቋም ሲሆን ለአገልግሎት ተቀባይ በዚህ ውል ሊይ ለተጠቀሰው ጊዜ እና ክፍያ ከፍሎ አገልግሎቱን በመፈለጉ ለተወሰነ ጊዜ አገልግሎት ተቀባይ በሚኖርበት ቤት ውስጥ አገሌግልቱን ለማግኘት በአገልግሎት ሰጪ እና በአገልግሎት ተቀባይ መካከሌ ለተወሰነ ጊዜ የተደረገ የአገልግሎት ስምምነት ነው፡፡

አንቀጽ ሁለት፡ ስምምነት
የሰራተኞች ቁጥር እንደ ደንበኛው የስራ ዓይነት እና መጠን በአገልግሎት ተቀባይ ጥያቄ መሰረት ከፍ እና ዝቅ የሚል ሆኖ አገልግሎት ሰጪ እያንዳንዱ ሰራተኛ የተመደበበት ስራ በተገቢው መንገድ በሚሰጠው የስራ መዘርዝር መሰረት በአገልግሎት ተቀባይ የሚከፈል የክፍያ መጠን-----------------ብር ለ--------------------ጊዜ አገልግሎቱን የሚያገኝ ይሆናል፡፡ አስፈሊጊ ሆኖ ከተገኘ ለሰራተኞቹ የጤና ዋስትና እንዲሁም ከስራ ጋር በተያያዘ ለሚፈጠር የጤና እክል የሚገባ የጤና ዋስትናና በስራ ቦታና ጊዜ ለሚደርስ አደጋ የሚገባውን የአደጋ ዋስትና (Work related health and accident insurance) የሚሸፈነው በአገልግሎት አቅራቢው ድርጅት ነው፡፡

አንቀጽ ሦስት፡ የአገልግሎት አቅራቢ ግዳታዎች
3.1 አገልግሎት አቅራቢ ከአገልግሎት ተቀባይ በተሰጠው የስራ መዘርዘሮች (specification) መሰረት ሰራተኞቹን ከልዩ በተጠቀሰው ዋጋ ያቀርባል፡፡
3.2 የአገልግሎት አቅራቢ በውል የተካተቱትን ሰራተኞች ብቃት እንደተጠበቀ ሆኖ ክፍተት በሚፈጠር ጊዜ በተጠየቀ በ48 ሰአት ለአገልግሎት ተቀባይ ይተካል፡፡
3.3 አገልግሎት አቅራቢ ለአገልግሎት ተቀባይ የሰራተኞቹን የስም ዝርዝር በየስራ መደቡ በጽሁፍ ያስረክባል፡፡
3.4 አገልግሎት አቅራቢ የሚያቀርባቸውን ሰራተኞችን በተመለከተ፡፡
 3.4.1 አገልግሎት አቅራቢው የሚመደባቸው ሰራተኞች ስራ ከመጀመራታቸው በፊት ስለ ስራው አጠቃላይ ሁኔታ፣ ስለሚጠበቅባቸው የስራ ልምድና ስነ-ሥርዓት ተገቢው ማስገንዘቢያ "orientation" እንዲሰጣቸው ኃላፊነት አለበት፡፡
 3.4.2 ሰራተኛው ከተመደበበት ስራ ጋር በተያያዘ ሊያደርሰው የሚችለውን ማንኛውም ዓይነት ጉዳት ወይም የመብት ጥያቄ በፈጠረ ጊዜ አቅራቢው ድርጅት በሙሉ ተጠያቂ ይሆናል፡፡
 3.4.3 በስራ መደቡ ከተጠቀሰው የሰራተኛ ብዛት በታች ወይም በላይ ማቅረብ አይፈቀድም፡፡
 3.4.4 የብቃት ማነስ፣ የጤና ችግር ያላቸውንና ማንኛውም አይነት ሱስ ተገዢ የሆኑ ሰራተኞችን ማቅረብ አይቻልም፡፡ መሰረታዊ ብቃት የሌላቸው ሰራተኞች ቢቀርቡና ቅሬታ ቢደርስ፣ አዲስ ብቃት ያላቸው ሰራተኞች በ48 ሰአት ውስጥ በአገልግሎት አቅራቢ ይተካሉ፡፡
 3.4.5 አገልግሎት አቅራቢው ለአገልግሎት ተቀባይ የሚሰጠውን አገልግሎት በቀጣይ ክትትል በማድረግ እንዲያግዝ በአካላዊ ተቆጣጣሪ ወይም በስልክ ክትትል ይፈጽማል፡፡
 3.4.6 አገልግሎት ተቀባይ 50% የአገልግሎቱን ክፍያ በውል በፈረመበት ቀን ይከፍላል፣ የቀረው 50% ደግሞ አገልግሎት ሰራተኞች ስራ ሲጀምሩ ይከፍላል፡፡
3.5 አገልግሎት አቅራቢው የሚያቀርባቸው ሰራተኞች እድሜ ከ20 ዓመት እስከ 60 ዓመት ባለው ዕድሜ ገደብ ውስጥ መሆን አለባቸው፡፡
3.6 አገልግሎት አቅራቢ በሚመደባቸው ሰራተኞች ምክንያት አገልግሎት ተቀባይ ተገቢውን አገልግሎት ሳያገኝ ቢቀር፣ የተሰጠውን አገልግሎት ቀናት ብቻ ታስበው ይመለሳል፡፡
3.7 አገልግሎት ተቀባይ በራሱ ምክንያት የተመደበለትን አገልግሎት ሰጪ ሰራተኛ ካልቀበለ፣ ውልን በተሰናበተበት ጊዜ የከፈለውን ክፍያ መመለስ አይችልም፡፡ (ከህክምና ጋር የተያያዘ ጉዳይ ውጭ)

አንቀጽ አራት፡ አገልግሎት ተቀባይ ግዳታዎች
4.1 በውል መሰረት አስፈላጊ አገልግሎት ሲያገኝ የአገልግሎት ክፍያውን መክፈል አለበት፡፡
4.2 አገልግሎት አቅራቢው የሚያቀርባቸውን ሰራተኞች የሚመደቡትን አካባቢ ስም ለአገልግሎት ተቀባይ አስቀድመው በጽሁፍ ወይም በስልክ ማሳወቅ አለበት፡፡
4.3 ማንኛውም ለስራ የሚያስፈልጉ መሳሪያዎች በወቅቱ ማቅረብ አለበት፡፡
4.4 የማረፊያና የልብስ መቀየሪያ ቦታ አገልግሎት ማቅረብ አለበት፡፡
4.5 አገልግሎት ተቀባይ ተጨማሪ የአገልግሎት ጊዜ ከፈለገ ለአገልግሎት ሰጪ የጽሁፍ መልዕክት በመልክ ወይም በስልክ ያሳውቃል፡፡
4.6 አገልግሎት ተቀባይ አገልግሎት ሰጪ ሰራተኞች በሥራ ሲመደቡ እንደ ወርቅ፣ አለማዝ እና ሌሎች የከበሩ ዋጋ ያላቸው ጌጣ ጌጦችን በተገቢው መንገድ ማጠበቅና መጠበቅ ኃላፊነት አለበት፡፡
 4.6.1 አገልግሎት ተቀባይ አገልግሎት ሰጪ ሰራተኞች በሥራ ሲመደቡ በተራ ቁጥር 4.6 ውስጥ ከተገለጹት ውጪ ያሉ ላልች ማንኛውም ንብረት በተገቢው መንገድ ማጠበቅና መጠበቅ ኃላፊነት አለበት፡፡
4.7 በተራ ቁጥር 4.6 ውስጥ በተገለጹት መሠረት አገልግሎት ተቀባይ ተገቢውን ጥንቃቄ ሳይያድርግ ቢቀር ኃላፊነቱን የሚወስደው ነው፡፡
 4.7.1 በተራ ቁጥር 4.6.1 ውስጥ በተገለጸው መሠረት አገልግሎት ተቀባይ ተገቢውን ጥንቃቄ አድርጎ የሚከሰት የንብረት መጥፋት በአገልግሎት ሰጪ ሰራተኞች ኃላፊነት ይወሰዳል፡፡
4.8 አገልግሎት ተቀባይ የተመደቡትን ሰራተኞችን በራሱ ይዞ መቀጠል የሚፈልግ ከሆነ ከአገልግሎት አቅራቢ የተሰጠውን አገልግሎት 1/3 (አንዴ ሶስተኛውን) ክፍያ ለአገልግሎት ሰጪ ይከፍላል፡፡
4.9 በተራ ቁጥር 4.8 መሠረት አገልግሎት ተቀባይ የተመደበውን ሰራተኛ በራሱ ይዞ የሚቀጠል ከሆነ እና በመካከላቸው ለሚፈጠሩ ማንኛውም አልመግባባቶች ወይም የተመደበው ሰራተኛ ለሚያጠፋው ጥፋት አገልግሎት አቅራቢ ኃላፊነት አይወስድም፡፡
4.10 አገልግሎት ተቀባይ ቅድመ ክፍያ ከከፈለ በኃላ በራሱ ምክንያት አገልግሎቱን ካቋረጡ 25% ውል ማቋረጫ ቅጣት ይከፍላል፡፡
4.11 ዕለታዊ ምግብ ተመላላሽ ሞግዚቶች ከቤታቸው ቋጥረው የሚመጡ ይሆናል፡፡ ትኩስ ነገሮችን ጊዜያዊ ንፅህና መጠበቂያ አስፈላጊ የሆኑ ቁሳቁሶችን ለማዘጋጀት አገልግሎት ተቀባይ ግዳታ ይሰጣል፡፡

አንቀጽ አምስት፡ የውሉ አካል ሆነው ስለሚቆጠሩ ሰነድች
5.1 አገልግሎት አቅራቢው አገልግሎቱን እንደሚያቀርብ የሚገልጽ በአገልግሎት ተቀባይ የተጻፈው ደብዳቤ (letter of awards) ወይም ሌሎች መጠይቆች
5.2 በአገልግሎት ተቀባይ የተዘጋጀው የሰራተኞች የስራ መዘርዝር የዚህ ውል አካል ነው፡፡

አንቀጽ ስድስት፡ በውሉ አፈጻጸም ሊይ ተፈጻሚ ስለሚሆኑ ህጎች
በዚህ ውል ውስጥ ባለተሸፈኑ ጉዲዮች ሊይ አግባብነት ያላቸው የኢትዮጵያ የፍትሀብሄር ህግና የንግዴ ህግ ተፈጻሚ ይሆናለ፡፡

አንቀጽ ሰባት፡ ውል የሚቋረጥባቸው ምክንያቶች
7.1. አገልግሎት ተቀባዩ የሚፈልጋቸውን ምትክ ሰራተኞችን እንዲያቀርብለት አገልግሎት አቅራቢውን በጠየቀው በ48 ሰአት ውስጥ በተደጋጋሚ ማቅረብ ያልቻለ እንደሆነ
7.2. አገልግሎት አቅራቢው ያሰማራቸውን ሰራተኞች በቅርበት መቆጣጠር ሳይችል ሲቀር
7.3. ማንኛውም የውሉን መንፈስ የሚቀይር ግዴታ አገልግሎት አቅራቢው ወይም አገልግሎት ተቀባይ ካቀረቡ እና በዚህ ውል ውስጥ የተጠቀሱት ማናቸውም አንቀጾች ተጥሰው ከተገኙ አንደኛው ወገን ለሌላኛው የ3 (ሦስት) ቀን ቅድሚያ ማስጠንቀቂያ በመስጠት ውልን ሊያቋርጥ ይችላል፡፡

አንቀጽ ስምንት፡ ውሉ የሚጸናበት ጊዜ
8.1. ይህ ውል ከ ………ወር-------- ቀን -------- ዓ.ም ጀምሮ ለ------------------ ቀናት የጸና ይሆናል፡፡ በአንቀጽ 7 ከተገለጹት ምክንያቶች ውጪ በሆነ መነሻ ውልን ለማፍረስ የሚፈለግ ወገን የ5 (የአምስት) ቀን የጽሁፍ ማስጠንቀቂያ በቅዴሚያ መስጠት ይኖርበታል፡፡

አንቀጽ ዘጠኝ፡ አለመግባባት ቢፈጠር
ይህ ውል የተፈጸመው የኢትዮጵያን የውል ህግ ዴንጋጌዎች አገናዝቦ በመሆኑ አለመግባባት ቢፈጠር በስምምነት እንዱያሌቅ ይደረጋል፡፡ በስምምነት መፍታት ባይቻል ግን መብቴን አስከብራለሁ የሚለው ወገን ከሊይ የተጠቀሱትን የውል አንቀጾች አግባብ ካለው ህግ ጋር በማገናዘብ የበኩል ህጋዊ እርምጃ ይወስዳል፡፡
"""

# --- FULL ENGLISH TERMS ---
TERMS_EN = """
📋 **SERVICE AGREEMENT**

This service agreement is between AGOS Postpartum Care ("Service Provider") Address: Addis Ababa, Ethiopia, Sub City: Arada, Woreda: 02, House No.: 613, Tel: 0967621545, hereinafter "Service Provider".

And Mr/Ms ______________________________ Address __________ Sub City ________ Woreda ______ House No. ______ Tel No. __________, hereinafter "the Client".

Article One: About Terms
The Service Provider provides the following services: Welcoming Decor (for the mother return home), Nanny Services (daytime and/or nighttime care for newborn), Chef Checkups (nutritious meals tailored to postpartum recovery), Nurse Checkups (basic maternal and newborn health checks) and certified Nutritionist Guidance, Professional Postpartum Massage. All this service is provided by the service provider the client shall order and select the services and paid by the employee the numbers and services the client shall pay per employee.

Article Two: Service Provider Obligations
2.1 Service provider offers the employees in accordance with the specific price.
2.2 If the assigned worker is absent, the service provider will replace them within 48 hours upon request.
2.3 Service Provider provides the client with the assigned workers' name list in writing.
2.4 Regarding the service provider’s workers:
 2.4.1 Before engagement, the service provider is responsible for providing proper orientation regarding general work conditions.
 2.4.2 The service provider is fully responsible for any damage or rights issues related to assigned workers.
 2.4.3 It is not permitted to provide fewer or more employees than specified in the job description.
 2.4.4 Workers must be competent, healthy, and free from addiction. If complaints arise, a qualified replacement will be provided within 48 hours.
 2.4.5 The service provider will assign a controller or maintain phone contact as needed to assist services.
 2.4.6 The client will pay 50% advance on the signed contract date, and the remaining payment on the assigned worker’s start date.
 2.4.7 Assigned workers must be between 20 and 60 years old.
 2.4.8 If appropriate service is not received, only the days of service provided will be charged; the remaining amount will be refunded.
 2.4.9 If the client rejects workers without valid reason, payment is non-refundable.

Article Three: Client Obligations
3.1 Pay the service fee when the service is rendered as per the contract.
3.2 Inform the service provider in writing or by telephone of the client’s residence location.
3.3 Provide all necessary equipment required for the service.
3.4 Provide a clothing change area for workers.
3.5 Notify the service provider if additional service time is required.
3.6 The client is responsible for storing and safeguarding valuables such as jewelry, gold, and diamonds.
 3.6.1 The client is responsible for safeguarding any other property not mentioned above when service providers are assigned.
3.7 The service provider is not responsible for losses due to client negligence.
 3.7.1 If due care is taken, the organization is liable for any loss caused by the service provider’s employees.
3.8 If the client continues the service independently, one-third of the fee is payable to the service provider.
3.9 If the client continues with assigned workers independently, the service provider is not responsible for damages or disagreements.
3.10 If the service is canceled after paying the advance, a 25% cancellation fee applies.
3.11 Daily meals are provided by caregivers from their homes; the client must provide hygiene materials and hot drinks.

Article Four: Annex
4.1 LETER OF THE AWARDS(AWARDS) or other questionnaires/documents related to the service.
4.2 The employee's job description is part of this contract.

Article Five: Governing Laws
Under this contract is not covered the Ethiopian Civil and business law enforced in unexpected issues.

Article Six: Grounds of Termination
6.1 If the client requests services, the provider will respond within 24 hours.
6.2 When the service provider is unable to control employees.
6.3 One side of the obligations that any of the obligations of the commencer invites the service provider or any of the paragraphs quoted in the contract can also end the contract by giving the other 3 (three days) writing notice.

Article Seven: Contract Period
This Contract is effective from --------------------, up to ------------------- valid. In accordance article six A party who wants to break the contract with the above reasons must be give writing notice 5 (five) day of which you want to break the contract in some of the reasons.

Article Eight: Settlement of Disputes
Any dispute arising out of or in connection with this agreement shall be amicably settled by the two parties through negotiation. If the case is not settled amicably through negotiation, the dispute shall be settled by Ethiopian regular federal competent court.
"""

# --- PDF GENERATOR WITH LOGO ---
def create_intake_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add Logo if it exists
    y_start = height - 50
    if os.path.exists(LOGO_PATH):
        try:
            logo = ImageReader(LOGO_PATH)
            # Draws logo at top right, scaled to 60x60
            c.drawImage(logo, 480, height - 80, width=60, height=60, mask='auto')
        except Exception:
            pass # Skip if image is corrupted

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Agos Postpartum Care")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, "Official Intake Confirmation Form")
    c.line(50, height - 85, 550, height - 85)

    # Content
    c.setFont("Helvetica", 11)
    y_position = height - 120

    for key, value in data.items():
        if key.startswith('p_') and key not in ['history', 'p_id_file']:
            label = key[2:].replace('_', ' ').upper()
            text = f"{label}: {value}"
            c.drawString(50, y_position, text)
            y_position -= 25
            if y_position < 60:
                c.showPage()
                y_position = height - 50

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 40, "Generated via Agos Telegram Bot. Verified submission.")
    c.save()
    buffer.seek(0)
    return buffer

# --- HELPERS ---
async def send_terms(update, text, keyboard):
    chunks = [text[i:i+3800] for i in range(0, len(text), 3800)]
    target = update.callback_query.message if update.callback_query else update.message
    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            await target.reply_text(chunk, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await target.reply_text(chunk, parse_mode='Markdown')

def get_back_kb(lang):
    return InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='p_back')]])

# --- NAVIGATION ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
                [InlineKeyboardButton("አማርኛ 🇪🇹", callback_data='lang_am')]]
    target = update.message if update.message else update.callback_query.message
    await target.reply_text("🌿 Choose Language / ቋንቋ ይምረጡ:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str = None):
    if lang: context.user_data['lang'] = lang
    else: lang = context.user_data.get('lang', 'en')

    btns = CONTENT[lang]['btns']
    keyboard = [
        [InlineKeyboardButton(btns[0], callback_data='info_care'), InlineKeyboardButton(btns[1], callback_data='info_decor')],
        [InlineKeyboardButton(btns[2], callback_data='info_arrival'), InlineKeyboardButton(btns[3], callback_data='info_media')],
        [InlineKeyboardButton(btns[5], callback_data='p_start'), InlineKeyboardButton(btns[6], callback_data='d_start')],
        [InlineKeyboardButton(btns[4], callback_data='info_contact'), InlineKeyboardButton(CONTENT[lang]['change_lang'], callback_data='restart')]
    ]
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(CONTENT[lang]['welcome'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text(CONTENT[lang]['welcome'], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def info_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    choice = query.data.replace('info_', '')
    text = CONTENT[lang].get(f'{choice}_text', "Information coming soon...")
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]])
    await query.message.edit_text(text, reply_markup=back_btn, parse_mode='Markdown')

# --- INTAKE FLOW (WITH PRESERVED LOGIC) ---
# Updated Intake Start
# Updated Intake Start with Exit Button
async def p_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    context.user_data['history'] = []
    kb = [
        [InlineKeyboardButton(CONTENT[lang]['agree_btn'], callback_data='p_agree')],
        [InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]
    ]
    await send_terms(update, TERMS_EN if lang == 'en' else TERMS_AM, InlineKeyboardMarkup(kb))
    return P_TERMS

async def p_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    history = context.user_data.get('history', [])
    if not history: return await start(update, context)
    last_state = history.pop()
    state_to_func = {
        P_NAME: p_q1, P_ADDR: p_q2, P_AGE: p_q3, P_PHONE: p_q4, P_EDD: p_q5,
        P_W_BEFORE: p_q6, P_W_NOW: p_q7, P_BIRTH: p_q8, P_GENDER: p_q9,
        P_DIET: p_q10, P_RISK: p_q11, P_ALLERGY: p_q12, P_BREASTFEED: p_q13,
        P_LANG_PREF: p_q14, P_NOTES: p_q15, P_HOME: p_q16, P_PACKAGE: p_q17, P_ID: p_q18
    }
    return await state_to_func[last_state](update, context)

# All Intake functions p_q1 to p_q18 from previous step are preserved here...
# [Included in the main script logic below for full functionality]

async def p_q1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text("1. Full Name / ሙሉ ስም:", reply_markup=ReplyKeyboardRemove())
    return P_NAME

async def p_q2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_name'] = update.message.text
        context.user_data['history'].append(P_NAME)
    await (update.message or update.callback_query.message).reply_text("2. Address / አድራሻ:", reply_markup=get_back_kb(lang))
    return P_ADDR

async def p_q3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_addr'] = update.message.text
        context.user_data['history'].append(P_ADDR)
    await (update.message or update.callback_query.message).reply_text("3. Age / እድሜ:", reply_markup=get_back_kb(lang))
    return P_AGE

async def p_q4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_age'] = update.message.text
        context.user_data['history'].append(P_AGE)
    await (update.message or update.callback_query.message).reply_text("4. Phone Number / ስልክ:", reply_markup=get_back_kb(lang))
    return P_PHONE

# Updated Intake Date Format Question
async def p_q5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_phone'] = update.message.text
        context.user_data['history'].append(P_PHONE)

    text = ("5. Expected Due Date (EDD):\nFormat: (dd/mm/yyyy)\nExample: 12/10/2016" if lang == 'en'
            else "5. የሚጠበቅበት የወሊድ ቀን:\nአጻጻፍ: (ቀን/ወር/ዓመት)\nምሳሌ: 12/10/2016")

    await (update.message or update.callback_query.message).reply_text(text, reply_markup=get_back_kb(lang))
    return P_EDD

async def p_q6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_edd'] = update.message.text
        context.user_data['history'].append(P_EDD)
    await (update.message or update.callback_query.message).reply_text("6. Weight Before Pregnancy (Kg):", reply_markup=get_back_kb(lang))
    return P_W_BEFORE

async def p_q7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_w_b'] = update.message.text
        context.user_data['history'].append(P_W_BEFORE)
    await (update.message or update.callback_query.message).reply_text("7. Current Weight (Kg):", reply_markup=get_back_kb(lang))
    return P_W_NOW

async def p_q8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_w_n'] = update.message.text
        context.user_data['history'].append(P_W_NOW)
    kb = [[InlineKeyboardButton("Normal", callback_data='Normal'), InlineKeyboardButton("Cesarean", callback_data='C-Sec')],
          [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='p_back')]]
    await (update.message or update.callback_query.message).reply_text("8. Delivery Type:", reply_markup=InlineKeyboardMarkup(kb))
    return P_BIRTH

async def p_q9(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.callback_query and update.callback_query.data != 'p_back':
        context.user_data['p_birth'] = update.callback_query.data
        context.user_data['history'].append(P_BIRTH)
    kb = [[InlineKeyboardButton("Male", callback_data='M'), InlineKeyboardButton("Female", callback_data='F')],
          [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='p_back')]]
    await (update.message or update.callback_query.message).reply_text("9. Baby Gender:", reply_markup=InlineKeyboardMarkup(kb))
    return P_GENDER

async def p_q10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.callback_query and update.callback_query.data != 'p_back':
        context.user_data['p_gender'] = update.callback_query.data
        context.user_data['history'].append(P_GENDER)
    await (update.message or update.callback_query.message).reply_text("10. Dietary Preference:", reply_markup=get_back_kb(lang))
    return P_DIET

async def p_q11(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_diet'] = update.message.text
        context.user_data['history'].append(P_DIET)
    await (update.message or update.callback_query.message).reply_text("11. Pregnancy Complications:", reply_markup=get_back_kb(lang))
    return P_RISK

async def p_q12(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_risk'] = update.message.text
        context.user_data['history'].append(P_RISK)
    await (update.message or update.callback_query.message).reply_text("12. Allergies:", reply_markup=get_back_kb(lang))
    return P_ALLERGY

async def p_q13(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_allergy'] = update.message.text
        context.user_data['history'].append(P_ALLERGY)
    kb = [[InlineKeyboardButton("Yes", callback_data='Yes'), InlineKeyboardButton("No", callback_data='No')],
          [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='p_back')]]
    await (update.message or update.callback_query.message).reply_text("13. Breastfeeding?", reply_markup=InlineKeyboardMarkup(kb))
    return P_BREASTFEED

async def p_q14(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.callback_query and update.callback_query.data != 'p_back':
        context.user_data['p_breast'] = update.callback_query.data
        context.user_data['history'].append(P_BREASTFEED)
    await (update.message or update.callback_query.message).reply_text("14. Preferred Language:", reply_markup=get_back_kb(lang))
    return P_LANG_PREF

async def p_q15(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_lang'] = update.message.text
        context.user_data['history'].append(P_LANG_PREF)
    await (update.message or update.callback_query.message).reply_text("15. Additional Notes:", reply_markup=get_back_kb(lang))
    return P_NOTES

async def p_q16(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.message:
        context.user_data['p_notes'] = update.message.text
        context.user_data['history'].append(P_NOTES)
    kb = [[InlineKeyboardButton("Villa", callback_data='Villa'), InlineKeyboardButton("Apt", callback_data='Apt')],
          [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='p_back')]]
    await (update.message or update.callback_query.message).reply_text("16. House Type:", reply_markup=InlineKeyboardMarkup(kb))
    return P_HOME

async def p_q17(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.callback_query and update.callback_query.data != 'p_back':
        context.user_data['p_home'] = update.callback_query.data
        context.user_data['history'].append(P_HOME)
    kb = [[InlineKeyboardButton("Full 40", callback_data='Full40'), InlineKeyboardButton("Half 30", callback_data='Half30')],
          [InlineKeyboardButton(CONTENT[lang]['q_back'], callback_data='p_back')]]
    await (update.message or update.callback_query.message).reply_text("17. Package Selection:", reply_markup=InlineKeyboardMarkup(kb))
    return P_PACKAGE

async def p_q18(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'en')
    if update.callback_query and update.callback_query.data != 'p_back':
        context.user_data['p_pkg'] = update.callback_query.data
        context.user_data['history'].append(P_PACKAGE)
    await (update.message or update.callback_query.message).reply_text("18. Upload National ID Photo:", reply_markup=get_back_kb(lang))
    return P_ID

async def p_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo: return P_ID
    id_img = update.message.photo[-1].file_id
    pdf_file = create_intake_pdf(context.user_data)

    report = "🚨 **NEW INTAKE** 🚨\n\n" + "\n".join([f"🔹 {k[2:].upper()}: {v}" for k, v in context.user_data.items() if k.startswith('p_') and k != 'history'])

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=id_img, caption=f"ID ATTACHED\n\n{report}", parse_mode='Markdown')
    await context.bot.send_document(chat_id=ADMIN_ID, document=pdf_file, filename=f"Intake_{context.user_data.get('p_name','Agos')}.pdf")

    pdf_file.seek(0)
    await update.message.reply_document(document=pdf_file, filename="Agos_Intake_Confirmation.pdf", caption="✅ Application submitted! Above is your receipt.")

    await show_menu(update, context)
    return ConversationHandler.END

# --- DECOR FLOW (Simplified) ---
# --- FIXED DECOR FLOW ---
# Updated Decor Start
# Updated Decor Start with Exit Button
async def d_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    await query.answer()
    kb = [[InlineKeyboardButton(CONTENT[lang]['back'], callback_data='menu')]]
    await query.message.reply_text("🎁 **Decor Booking**\n\n1. Full Name / ሙሉ ስም:", reply_markup=InlineKeyboardMarkup(kb))
    return D_NAME

async def d_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_name'] = update.message.text
    kb = [[InlineKeyboardButton("Male", callback_data='Male'), InlineKeyboardButton("Female", callback_data='Female')],
          [InlineKeyboardButton("Not Sure", callback_data='NotSure')]]
    await update.message.reply_text("2. Gender of the Newborn:", reply_markup=InlineKeyboardMarkup(kb))
    return D_GENDER

async def d_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['d_gender'] = query.data
    await query.message.reply_text("3. House Address for Decor Setup:")
    return D_ADDR

async def d_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_addr'] = update.message.text
    await update.message.reply_text("4. Client Phone Number:")
    return D_PHONE

async def d_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_phone'] = update.message.text
    await update.message.reply_text("5. Contact Person at Home (if different):")
    return D_CONTACT

async def d_step5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_contact'] = update.message.text
    kb = [[InlineKeyboardButton("Home Decor - 15,000 ETB", callback_data='15k')],
          [InlineKeyboardButton("Home Decor Deluxe - 20,000 ETB", callback_data='20k')],
          [InlineKeyboardButton("Home Decor Premium - 25,000 ETB", callback_data='25k')]]
    await update.message.reply_text("6. Chosen Surprise Package:", reply_markup=InlineKeyboardMarkup(kb))
    return D_PKG

async def d_step6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['d_pkg'] = query.data
    await query.message.reply_text("7. Preferred Decor Date & Time\nFormat: (dd/mm/yyyy), (Time in LT)\nExample: 12/10/2016, 8:00 LT")
    return D_DATE

async def d_step7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_date'] = update.message.text
    kb = [[InlineKeyboardButton("Villa", callback_data='Villa'), InlineKeyboardButton("Apartment", callback_data='Apt')],
          [InlineKeyboardButton("Condo", callback_data='Condo')],
          [InlineKeyboardButton("G+1", callback_data='G1'), InlineKeyboardButton("G+2", callback_data='G2')]]
    await update.message.reply_text("8. House Type:", reply_markup=InlineKeyboardMarkup(kb))
    return D_HOUSE

async def d_step8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['d_house'] = query.data
    await query.message.reply_text("9. Special Notes (Limousine, Photo, Video, or None):")
    return D_NOTES

async def d_step9(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['d_notes'] = update.message.text
    await update.message.reply_text("10. Finally, upload your Payment Screenshot:")
    return D_PAYMENT

async def d_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please upload a photo.")
        return D_PAYMENT

    pay_img = update.message.photo[-1].file_id
    summary = (f"🔔 **NEW AGOS BOOKING**\n\n"
               f"👤 Name: {context.user_data.get('d_name')}\n"
               f"👶 Baby: {context.user_data.get('d_gender')}\n"
               f"📞 Phone: {context.user_data.get('d_phone')}\n"
               f"🏠 Address: {context.user_data.get('d_addr')}\n"
               f"🏗️ House: {context.user_data.get('d_house')}\n"
               f"🎁 Pkg: {context.user_data.get('d_pkg')}\n"
               f"📅 Date: {context.user_data.get('d_date')}\n"
               f"📝 Notes: {context.user_data.get('d_notes')}")

    await context.bot.send_photo(chat_id=ADMIN_ID, photo=pay_img, caption=summary, parse_mode='Markdown')
    await update.message.reply_text("✅ Order Received! We will contact you shortly.")
    await show_menu(update, context)
    return ConversationHandler.END

# --- APP RUNNER ---

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()

    p_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(p_start, pattern='^p_start$')],
        states={
            P_TERMS: [CallbackQueryHandler(p_q1, pattern='^p_agree$')],
            P_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q2), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q3), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q4), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q5), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_EDD: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q6), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_W_BEFORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q7), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_W_NOW: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q8), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_BIRTH: [CallbackQueryHandler(p_q9), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_GENDER: [CallbackQueryHandler(p_q10), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_DIET: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q11), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_RISK: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q12), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_ALLERGY: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q13), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_BREASTFEED: [CallbackQueryHandler(p_q14), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_LANG_PREF: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q15), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_q16), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_HOME: [CallbackQueryHandler(p_q17), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_PACKAGE: [CallbackQueryHandler(p_q18), CallbackQueryHandler(p_back_handler, pattern='^p_back$')],
            P_ID: [MessageHandler(filters.PHOTO, p_final), CallbackQueryHandler(p_back_handler, pattern='^p_back$')]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(show_menu, pattern='^menu$'), CallbackQueryHandler(start, pattern='^restart$')],
        allow_reentry=True
    )

    d_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(d_start, pattern='^d_start$')],
        states={
            D_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step1)],
            D_GENDER: [CallbackQueryHandler(d_step2)],
            D_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step3)],
            D_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step4)],
            D_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step5)],
            D_PKG: [CallbackQueryHandler(d_step6)],
            D_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step7)],
            D_HOUSE: [CallbackQueryHandler(d_step8)],
            D_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, d_step9)],
            D_PAYMENT: [MessageHandler(filters.PHOTO, d_final)]
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(show_menu, pattern='^menu$'), CallbackQueryHandler(start, pattern='^restart$')],
        allow_reentry=True
    )

    app.add_handler(p_conv)
    app.add_handler(d_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lambda u, c: show_menu(u, c, u.callback_query.data.split('_')[1]), pattern='^lang_'))
    app.add_handler(CallbackQueryHandler(lambda u, c: show_menu(u, c), pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(info_pages, pattern='^info_'))
    app.add_handler(CallbackQueryHandler(start, pattern='^restart$'))

    print("Agos Bot is live...")
    app.run_polling()