import pandas as pd
import random
from datetime import datetime, timedelta

# Load country, region, and city data from the CSV file
cities_df = pd.read_csv("country_region_city.csv")

# Generate a list of products and materials with consistent pricing across regions
num_products = 50
num_materials = 50
products = [f"Product_{i+1}" for i in range(num_products)]
materials = [f"MAT_{i:03}" for i in range(1, num_materials + 1)]

# Initialize master list data for products and materials
masterlist_data = []

# Create product-material combinations with specified constraints
for _, location_row in cities_df.iterrows():
    country = location_row['Country']
    region = location_row['Region']
    city = location_row['City']

    for product in products:
        # Set a single base price for the product, consistent within the store
        product_price = round(random.uniform(20, 100), 2)

        # Set 5 to 8 random materials per product
        num_materials_per_product = random.randint(5, 8)
        selected_materials = random.sample(materials, num_materials_per_product)
        
        # Distribute material cost and shipping constraints for each material
        total_material_cost = round(product_price * random.uniform(0.3, 0.95), 2)
        total_material_shipping_cost = round(total_material_cost * random.uniform(0.05, 0.1), 2)
        
        # Ensure consistent costs across locations with minor variance for region
        for material_code in selected_materials:
            base_material_unit_cost = round(total_material_cost / num_materials_per_product, 2)
            region_adjusted_material_cost = round(base_material_unit_cost * random.uniform(0.97, 1.03), 2)
            material_quantity = random.randint(1, 20)
            material_shipping_cost = round(min(total_material_shipping_cost / num_materials_per_product, region_adjusted_material_cost * 0.1), 2)

            # Append each material to the master list
            masterlist_data.append({
                "Country": country,
                "Region": region,
                "City": city,
                "Product Name": product,
                "Product Price": product_price,
                "Material Code": material_code,
                "Material Quantity": material_quantity,
                "Material Unit Cost": region_adjusted_material_cost,
                "Material Shipping Cost": material_shipping_cost
            })

# Convert master list to DataFrame
masterlist_df = pd.DataFrame(masterlist_data)

# Summarize material costs by product-location to confirm totals for validation
product_cost_summary = masterlist_df.groupby(['Country', 'Region', 'City', 'Product Name']).agg(
    total_material_cost=('Material Unit Cost', 'sum'),
    total_material_shipping_cost=('Material Shipping Cost', 'sum')
).reset_index()

# Add these summarized costs back to the masterlist_df
masterlist_df = pd.merge(masterlist_df, product_cost_summary, on=['Country', 'Region', 'City', 'Product Name'], how='left')

# Generate 1 million sales transactions using the master list as reference
sales_data = []
start_date = datetime.now() - timedelta(days=90)
date_range = [start_date + timedelta(days=i) for i in range(90)]
discount_codes = ['DISCOUNT10', 'DISCOUNT15', 'DISCOUNT20']
vehicle_plates = [f"Plate_{i+1}" for i in range(1, 4)]

cities_df = cities_df[cities_df["Country"]=='Australia']

print('creating transactions')
# Create 1 million random transactions
for _ in range(1000):  # Generate 1 million transactions
    random_location = cities_df.sample(1).iloc[0]
    sales_order_number = f"SO_{random.randint(100000, 999999)}"
    order_date = random.choice(date_range)
    sales_type = random.choice(['delivery', 'instore'])
    delivery_fee = 0 if sales_type == 'instore' else round(random.uniform(0, 5), 2)
    delivery_duration = random.randint(5, 45) if sales_type == 'delivery' else None  # Set delivery duration for delivery orders
    delivery_vehicle = random.choice(vehicle_plates) if sales_type == 'delivery' else None
    
    # Determine the number of products for this order (1 to 8)
    num_products_in_order = random.randint(1, 8)
    
    # Generate each product in the order
    for _ in range(num_products_in_order):
        random_product = masterlist_df[
            (masterlist_df['Country'] == random_location['Country']) &
            (masterlist_df['Region'] == random_location['Region']) &
            (masterlist_df['City'] == random_location['City'])
        ].sample(1).iloc[0]

        quantity = random.randint(1, 10)
        total_product_cost = round(random_product['Product Price'] * quantity, 2)
        material_cost = random_product['total_material_cost']
        material_shipping_cost = random_product['total_material_shipping_cost']

        # Append each product in the order to the sales data
        sales_data.append({
            "Country": random_location['Country'],
            "Region": random_location['Region'],
            "City": random_location['City'],
            "Store ID": random_location['store_id'],
            "Store Name": f"{random_location['City']} Store",
            "Sales Order Number": sales_order_number,
            "Sales Order Date": order_date,
            "Product Name": random_product['Product Name'],
            "Quantity": quantity,
            "Unit Price": random_product['Product Price'],
            "Total Product Cost": total_product_cost,
            "Material Cost": material_cost,
            "Shipping Cost": material_shipping_cost,
            "Total Cost": material_cost + material_shipping_cost,
            "Sales Type": sales_type,
            "Delivery Fee": delivery_fee,
            "Delivery Duration (mins)": delivery_duration,  # New field for delivery duration
            "Discount Code": random.choice(discount_codes) if random.random() < 0.5 else None,
            "Discount %": int(random.choice([10, 15, 20])) if random.random() < 0.5 else 0,
            "Delivery vehicle plate": delivery_vehicle
        })

# Convert to DataFrame
sales_df = pd.DataFrame(sales_data)

# Save the final datasets to CSV
masterlist_df.to_csv("unique_products_with_materials_masterlist.csv", index=False)
sales_df_au = sales_df[sales_df["Country"]=='Australia']
sales_df_au.to_excel("sales_df_au_sample.xlsx")

sales_df.to_csv("superstore_sales_transactions_sample.csv", index=False)

