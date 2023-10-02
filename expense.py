import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import ConversationHandler
import openpyxl
from openpyxl import Workbook
from datetime import datetime
import os
import subprocess
from telegram import InputFile


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, filename='logs.txt', filemode='w')

# Initialize the bot
updater = Updater(token='6387277193:AAF-2PVrLpfchzcxjNeGrdyCyggi0KgYnXI', use_context=True)
dispatcher = updater.dispatcher

# Dictionary to store user states
user_data = {}

# Command handler for /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Welcome to the expense bot!")

def add_expense(update: Update, context: CallbackContext) -> None:
    categories = ["Food", "Transportation", "Entertainment", "Housing", "Car", "Personal", "Gifts", "Health", "Education", "Sport\Body"]
    category_buttons = [InlineKeyboardButton(category, callback_data=category) for category in categories]
    
    # Create a list of lists, each containing one button
    buttons_per_row = 1  # Adjust the number of buttons per row if desired
    button_rows = [category_buttons[i:i+buttons_per_row] for i in range(0, len(category_buttons), buttons_per_row)]
    
    reply_markup = InlineKeyboardMarkup(button_rows)
    
    update.message.reply_text("Select a category:", reply_markup=reply_markup)
    return "SELECTING_CATEGORY"


# Handler for category selection
def select_category(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    category = query.data
    user_data[query.from_user.id] = {"category": category}
    
    subcategories = {
    "Food": ["Groceries", "Dining out"],
    "Transportation": ["Public transport", "Fuel"],
    "Entertainment": ["Movies", "Games"],
    "Housing": ["Rent", "Water", "Electricity", "Gas", "Taxes", "Internet", "Maintenance or repairs", "Cleaning", "Computer/Technology", "Other"],
    "Car": ["Test", "Public Transportation", "Roads", "Licensing", "Fuel", "Parking", "Garage", "Insurance", "Reports", "Other"],
    "Personal": ["Hair cut", "Clothing", "Technology", "Supplies", "Other"],
    "Gifts": ["Family", "Charity", "Partner", "Weddings", "Other"],
    "Health": ["Insurance", "Medications", "Medical Bills", "Advisers", "Other"],
    "Education": ["Tuition", "Books", "Courses", "Other"],
    "Sport\Body": ["Nutritionist", "Clothing", "Gym", "Sport Groups", "Physiotherapist", "Supplements", "Other"]
    }
    subcategory_buttons = [[InlineKeyboardButton(subcategory, callback_data=subcategory)] for subcategory in subcategories[category]]
    reply_markup = InlineKeyboardMarkup(subcategory_buttons)

    query.message.edit_text(f"You selected: {category}\nNow select a subcategory:", reply_markup=reply_markup)
    return "SELECTING_SUBCATEGORY"

# Handler for subcategory selection
def select_subcategory(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    subcategory = query.data
    user_id = query.from_user.id

    logging.info(f"Selected subcategory: {subcategory}")  # Add this line to log the selected subcategory

    user_data[user_id]["subcategory"] = subcategory
    query.message.edit_text(f"You selected: {user_data[user_id]['category']} - {subcategory}\nPlease enter the expense amount:")

    return "ENTERING_AMOUNT"

def save_expense_to_excel(user_id, date, amount, category, subcategory):
    file_name = f'user_{user_id}_expenses.xlsx'

    # Create a new workbook if the file doesn't exist
    if not os.path.exists(file_name):
        wb = openpyxl.Workbook()  
        ws = wb.active

        # Header row
        header = ['Date', 'Amount', 'Category', 'Subcategory']
        ws.append(header)
    else:
        wb = openpyxl.load_workbook(file_name)
        ws = wb.active

    # Append new row
    new_row = [date, amount, category, subcategory]
    ws.append(new_row)

    wb.save(file_name)  # Save the workbook

def enter_amount(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data[user_id]["amount"] = update.message.text

    # Get other expense details
    date = datetime.now().strftime('%Y-%m-%d')
    category = user_data[user_id]["category"]
    subcategory = user_data[user_id]["subcategory"]

    # Save expense details in user-specific Excel file
    save_expense_to_excel(user_id, date, user_data[user_id]["amount"], category, subcategory)

    update.message.reply_text("Expense saved successfully!")

    user_data[user_id] = {}  # Clear user data
    return

# Define conversation states
SELECTING_CATEGORY, SELECTING_SUBCATEGORY, ENTERING_AMOUNT = range(3)

# Define the conversation handler
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("addexpense", add_expense)],
    states={
        SELECTING_CATEGORY: [
            CallbackQueryHandler(select_category, pattern='^(Food|Transportation|Entertainment|Housing|Car|Personal|Gifts|Health|Education|Sport\\Body)$')
        ],
        SELECTING_SUBCATEGORY: [
            CallbackQueryHandler(select_subcategory, pattern='^(Groceries|Dining out|Public transport|Fuel|Movies|Games|Rent|Water|Electricity|Gas|Taxes|Internet|Maintenance or repairs|Cleaning|Computer/Technology|Other|Test|Public Transportation|Roads|Licensing|Fuel|Parking|Garage|Insurance|Reports|Other|Hair cut|Clothing|Technology|Supplies|Other|Family|Charity|Partner|Weddings|Other|Insurance|Medications|Medical Bills|Advisers|Other|Tuition|Books|Courses|Other|Nutritionist|Clothing|Gym|Sport Groups|Physiotherapist|Supplements|Other)$')
        ],
        ENTERING_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, enter_amount)],
    },
    fallbacks=[],
)

# Command handler for /recap
def run_recap(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_file_name = f'user_{user_id}_expenses.xlsx'

    logging.info(f"Running recap for user {user_id}")
    # Run the Python script that generates images
    subprocess.run(['python', 'analyze_script.py', user_file_name])
    
    logging.info(f"Recap images generated for user {user_id}")
    
    # Get the current month in the format 'YYYYMM'
    current_month = datetime.now().strftime('%Y%m')
    
    # Construct the paths to the user's images
    user_folder = f'user_{user_id}_images'
    images = [
        os.path.join(user_folder, 'expenses_by_category.png'),
        os.path.join(user_folder, f'expenses_pie_{current_month}.png')  # Replace with the correct month
    ]
    
    # Send images as responses
    for image_path in images:
        with open(image_path, 'rb') as image_file:
            context.bot.send_photo(chat_id=update.message.chat_id, photo=InputFile(image_file))





# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("addexpense", add_expense))
dispatcher.add_handler(CallbackQueryHandler(select_category, pattern='^(Food|Transportation|Entertainment|Housing|Car|Personal|Gifts|Health|Education|Sport\\Body)$'))
dispatcher.add_handler(CallbackQueryHandler(select_subcategory, pattern='^(Groceries|Dining out|Public transport|Fuel|Movies|Games|Rent|Water|Electricity|Gas|Taxes|Internet|Maintenance or repairs|Cleaning|Computer/Technology|Other|Test|Public Transportation|Roads|Licensing|Fuel|Parking|Garage|Insurance|Reports|Other|Hair cut|Clothing|Technology|Supplies|Other|Family|Charity|Partner|Weddings|Other|Insurance|Medications|Medical Bills|Advisers|Other|Tuition|Books|Courses|Other|Nutritionist|Clothing|Gym|Sport Groups|Physiotherapist|Supplements|Other)$'))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, enter_amount))
# Register the conversation handler
dispatcher.add_handler(conv_handler)
# Register the /recap command handler
dispatcher.add_handler(CommandHandler("recap", run_recap))
# Start the bot
updater.start_polling()
updater.idle()
