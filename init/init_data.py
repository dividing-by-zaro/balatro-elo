# init_data.py
import asyncio
import csv
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports from parent
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import connect_to_mongo, close_mongo_connection, get_database
from crud import create_card, get_card_count

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

async def load_cards_from_csv(csv_file=None):
    if csv_file is None:
        csv_file = SCRIPT_DIR / "jokers.csv"
    """Load cards from CSV file"""
    cards = []
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please ensure the file exists in the current directory.")
        return cards
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Verify required columns exist
            required_columns = ['name', 'image_url', 'description']
            missing_columns = [col for col in required_columns if col not in reader.fieldnames]
            
            if missing_columns:
                print(f"Error: {csv_file} must contain columns: {required_columns}")
                print(f"Missing columns: {missing_columns}")
                print(f"Found columns: {reader.fieldnames}")
                return cards
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is headers
                # Strip whitespace from values
                name = row['name'].strip() if row['name'] else ""
                image_url = row['image_url'].strip() if row['image_url'] else ""
                description = row['description'].strip() if row['description'] else ""
                
                # Skip rows with empty required fields
                if not name or not image_url:
                    print(f"Warning: Skipping row {row_num} - missing name or image_url")
                    continue
                
                # Description is optional, but warn if empty
                if not description:
                    print(f"Warning: Row {row_num} has empty description for card '{name}'")
                
                cards.append({
                    "name": name,
                    "image_url": image_url,
                    "description": description or "No description available"
                })
        
        print(f"Successfully loaded {len(cards)} cards from {csv_file}")
        
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
    
    return cards


async def reinitialize_database_from_csv():
    """Reinitialize the database with cards from jokers.csv, including description and default ELO"""
    await connect_to_mongo()
    
    try:
        # Load cards from CSV
        cards_data = await load_cards_from_csv()
        
        if not cards_data:
            print("No valid cards found in CSV file. Database reinitialization aborted.")
            return
        
        # Check if cards already exist
        card_count = await get_card_count()
        if card_count > 0:
            response = input(f"Database already has {card_count} cards. Do you want to clear and reinitialize? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Reinitialization cancelled.")
                return
            
            # Clear existing cards
            db = get_database()
            await db.Cards.delete_many({})
            await db.Comparisons.delete_many({})
            print(f"Cleared {card_count} existing cards and all comparisons.")
        
        print("Reinitializing database with cards from jokers.csv...")
        
        success_count = 0
        for card_data in cards_data:
            try:
                card = await create_card(
                    name=card_data["name"], 
                    image_url=card_data["image_url"],
                    description=card_data["description"]
                )
                print(f"Created card: {card.name} (ELO: {card.elo_rating})")
                success_count += 1
            except Exception as e:
                print(f"Error creating card '{card_data['name']}': {e}")
        
        print(f"Successfully reinitialized database with {success_count} out of {len(cards_data)} cards!")
        print("All cards start with ELO rating of 1200.")
        
    except Exception as e:
        print(f"Error during reinitialization: {e}")
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(reinitialize_database_from_csv())