from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
import sqlite3
import os
import traceback    #to track error
router = APIRouter()

# Set DB path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "crawler", "medicines.db")

# SQLite Connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Get raw table data
@router.get("/pharmeasy")
def get_pharmeasy_data():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM pharmeasy").fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.get("/apollo")
def get_apollo_data():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM apollo").fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Helpers to parse ₹price or %discount
def parse_price(price_str):
    if price_str:
        try:
            cleaned = str(price_str).strip().replace("₹", "").replace(",", "").replace("*", "")
            return float(cleaned)
        except Exception as e:
            print(f" Could not parse price: {price_str} → {e}")
            return None
    return None

def parse_discount(discount_str):
    if discount_str:
        try:
            cleaned = str(discount_str).lower().replace("off", "").replace("%", "").replace(" ", "")
            return float(cleaned)
        except Exception as e:
            print(f" Could not parse discount: {discount_str} → {e}")
            return None
    return 0.0

# Shared logic to return combined table
def fetch_combined_data_sorted(filter_by="price"):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM combined_data")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "name": row["name"],
            "brand": row["brand"],
            "source": row["source"],
            "price": row["price"],
            "discount": row["discount"],
            "best_price": row["best_price"],
            "best_offer": row["best_offer"]
        })

    if filter_by == "price":
        result = sorted(result, key=lambda x: parse_price(x["price"]) if x["price"] else float("inf"))
    elif filter_by == "discount":
        result = sorted(result, key=lambda x: parse_discount(x["discount"]) or 0.0, reverse=True)

    return result
@router.post("/api/reset-entry")
async def reset_entry(request: Request):
    try:
        data = request.json() if isinstance(request, dict) else await request.json()

        name = data.get("name")
        brand = data.get("brand")

        if not name or not brand:
            return JSONResponse(content={"error": "Missing name or brand"}, status_code=400)

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE combined_data
            SET best_price = NULL, best_offer = NULL
            WHERE name = ? AND brand = ?
        """, (name, brand))

        conn.commit()
        return JSONResponse(content={"status": "success"})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

    finally:
        if conn:
            conn.close()

@router.get("/create_and_update")
def get_combined_data(filter_by: str = Query("price", enum=["price", "discount"])):
    result = fetch_combined_data_sorted(filter_by)
    return JSONResponse(content=result)

# Combined view/update endpoint
@router.post("/create_and_update")
async def create_and_update(request: Request, filter_by: str = Query("price", enum=["price", "discount"])):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS combined_data (
        name TEXT,
        brand TEXT,
        price REAL,
        discount REAL,
        source TEXT,
        best_price REAL,
        best_offer REAL
    );
    """)

    # Insert if empty
    cursor.execute("SELECT COUNT(*) FROM combined_data")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO combined_data (name, brand, price, discount, source, best_price, best_offer)
        SELECT name, brand, price, discount, 'Pharmeasy', NULL, NULL FROM pharmeasy
        UNION ALL
        SELECT name, brand, price, discount, 'Apollo', NULL, NULL FROM apollo;
        """)


    try:
        body = {}
        if request.headers.get("content-length") and int(request.headers.get("content-length")) > 0:
            body = await request.json()

        def update_entry(name, brand, best_price, best_offer, force_clear=False):
            cursor.execute("SELECT price, discount FROM combined_data WHERE name=? AND brand=?", (name, brand))
            row = cursor.fetchone()
            if not row:
                print(f" No entry found for {name} ({brand})")
                return

            price = parse_price(row["price"])
            discount = parse_discount(row["discount"])
            mrp = None

            if price is None:
                print(f"❌ Skipping row for name={name}, brand={brand} due to bad price → price: {row['price']}")
                return

            if discount is None:
                print(f" Discount unparseable for {name} ({brand}) → '{row['discount']}', proceeding with only best_price")
                mrp = None
            else:
                if discount < 100:
                    try:
                        mrp = price / (1 - (discount / 100))
                    except Exception as e:
                        print(f" Error computing MRP for {name}: {e}")
                        mrp = None
            #  Clean and convert inputs
            def clean(value):
                if value in ("", None):
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None

            best_price = clean(best_price)
            best_offer = clean(best_offer)

            # Derive missing fields
            if not force_clear and mrp and (not "cb" in row["discount"].lower()):
                if best_price is not None and best_offer is None:
                    best_offer = round((1 - best_price / mrp) * 100, 2)
                elif best_offer is not None and best_price is None:
                    best_price = round(mrp * (1 - best_offer / 100), 2)

            print(f" name: {name}, brand: {brand}, price: {price}, discount: {discount}, best_price: {best_price}, best_offer: {best_offer}")

            print(f" Cleaned → best_price: {best_price} ({type(best_price)}), best_offer: {best_offer} ({type(best_offer)})")

            cursor.execute("""
                UPDATE combined_data
                SET best_price = ?, best_offer = ?
                WHERE name = ? AND brand = ?
            """, (None if best_price is None else best_price,None if  best_offer is None else best_offer, name, brand))

        #  Single update
        if isinstance(body, dict) and body.get("name") and body.get("brand"):
            update_entry(
                name=body.get("name"),
                brand=body.get("brand"),
                best_price=body.get("best_price"),
                best_offer=body.get("best_offer"),
                force_clear=body.get('force_clear', False)
                )

        #  Bulk updates
        elif isinstance(body, list):
            for entry in body:
                if entry.get("name") and entry.get("brand"):
                    update_entry(
                        name=entry.get("name"),
                        brand=entry.get("brand"),
                        best_price=entry.get("best_price"),
                        best_offer=entry.get("best_offer"),
                        force_clear=entry.get('force_clear', False)
                    )

        conn.commit()
        result = fetch_combined_data_sorted(filter_by)
        return JSONResponse(content=result)

    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

    finally:
        conn.close()

