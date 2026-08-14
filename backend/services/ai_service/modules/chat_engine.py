from backend.database import SessionLocal
from backend.services.sales_service.models.sale import Sale
from backend.services.inventory_service.models.medicine import Medicine
from backend.services.inventory_service.models.batch import Batch
from backend.services.inventory_service.models.outlet import Outlet
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from backend.services.ai_service.llm_service import query_llm


def detect_intent(query):
    """
    Enhanced intent detection with confidence scoring.
    Returns: (intent_name, confidence_score)
    """
    query = query.lower()

    intent_patterns = {
        "revenue": {
            "keywords": ["revenue", "income", "earnings", "sales value", "total sales"],
            "patterns": ["revenue", "earnings", "how much earned", "total income"],
            "confidence": 0.95
        },
        "sales_count": {
            "keywords": ["sales", "transactions", "orders", "how many", "count"],
            "patterns": ["total sales", "number of sales", "transactions", "how many sold"],
            "confidence": 0.90
        },
        "top_medicine": {
            "keywords": ["top", "most", "best", "sold", "popular", "selling"],
            "patterns": ["top selling", "most sold", "best medicine", "popular medicine"],
            "confidence": 0.92
        },
        "expiry": {
            "keywords": ["expire", "expiry", "expiring", "expired", "shelf life"],
            "patterns": ["expire", "expiry", "expiring soon", "shelf life", "batch expiry"],
            "confidence": 0.94
        },
        "stock": {
            "keywords": ["stock", "inventory", "quantity", "available", "low stock"],
            "patterns": ["stock level", "inventory", "how many in stock", "available quantity"],
            "confidence": 0.91
        },
        "restock": {
            "keywords": ["restock", "replenish", "reorder", "restocking", "low", "running out", "order"],
            "patterns": ["restock", "replenish", "reorder", "should i order", "need to order", "running low"],
            "confidence": 0.93
        },
        "outlet_performance": {
            "keywords": ["outlet", "pharmacy", "branch", "performance", "store", "location"],
            "patterns": ["outlet performance", "store sales", "branch comparison", "outlet wise"],
            "confidence": 0.89
        },
        "margin": {
            "keywords": ["margin", "profit", "profitability", "cost", "revenue"],
            "patterns": ["profit margin", "profitability", "gross margin", "net profit"],
            "confidence": 0.88
        }
    }

    scores = {}
    
    # Calculate confidence for each intent
    for intent, config in intent_patterns.items():
        score = 0
        # Check keywords
        keyword_matches = sum(1 for kw in config["keywords"] if kw in query)
        if keyword_matches > 0:
            score = config["confidence"] + (0.02 * keyword_matches)
        
        # Check patterns
        pattern_matches = sum(1 for pattern in config["patterns"] if pattern in query)
        if pattern_matches > 0:
            score = config["confidence"] + (0.03 * pattern_matches)
        
        if score > 0:
            scores[intent] = min(score, 1.0)
    
    # Return best match with confidence
    if scores:
        best_intent = max(scores, key=scores.get)
        return best_intent, scores[best_intent]
    
    return "unknown", 0.0


def format_revenue_response(revenue, outlet_count=None):
    """Format revenue response with insights."""
    if revenue is None:
        return "📊 No revenue data available yet."
    
    revenue = float(revenue) if revenue else 0
    avg_per_outlet = (revenue / outlet_count) if outlet_count and outlet_count > 0 else 0
    
    response = f"""
📊 **Revenue Analytics**
{'─' * 50}
Total Revenue: ₹{revenue:,.2f}
Outlets: {outlet_count if outlet_count else 'N/A'}
Avg per Outlet: ₹{avg_per_outlet:,.2f}

💡 **Insights:**
• Strong revenue generation across outlets
• Focus on maintaining consistent sales volume
• Track high-performing outlets for best practices
{'─' * 50}
"""
    return response.strip()


def format_sales_response(count, outlet_count=None):
    """Format sales count response with insights."""
    if count is None:
        return "📈 No sales data available yet."
    
    count = int(count) if count else 0
    avg_per_outlet = (count / outlet_count) if outlet_count and outlet_count > 0 else 0
    
    response = f"""
📈 **Sales Summary**
{'─' * 50}
Total Transactions: {count:,}
Active Outlets: {outlet_count if outlet_count else 'N/A'}
Avg Transactions/Outlet: {avg_per_outlet:.0f}

💡 **Insights:**
• Consistent transaction volume indicates healthy traffic
• Monitor outlet performance for optimization
• Maintain stock to support sales velocity
{'─' * 50}
"""
    return response.strip()


def format_top_medicine_response(medicines_list):
    """Format top medicines response with insights."""
    if not medicines_list:
        return "🏆 No sales data available yet."
    
    response = f"""
🏆 **Top 5 Best-Selling Medicines**
{'─' * 50}
"""
    
    for i, med in enumerate(medicines_list, 1):
        response += f"{i}. {med['name'].upper()}\n"
        response += f"   Quantity Sold: {med['quantity']:,} units\n"
        response += f"   Revenue: ₹{med['revenue']:,.2f}\n"
        response += f"   Profit: ₹{med['profit']:,.2f}\n\n"
    
    response += f"""
{'─' * 50}
💡 **Insights:**
• These medicines drive majority of revenue
• Ensure priority stock for top performers
• Monitor demand to prevent stockouts
{'─' * 50}
"""
    
    return response.strip()


def format_expiry_response(expired_batches, expiring_batches):
    """Format expiry tracking response with alerts."""
    
    response = f"""
⏰ **Expiry Tracking Report**
{'─' * 50}
"""
    
    if expired_batches:
        response += f"\n🚨 **EXPIRED BATCHES ({len(expired_batches)}):**\n"
        for batch in expired_batches:
            response += f"   • {batch['medicine_name']} (Batch: {batch['batch_number']})\n"
            response += f"     Expiry: {batch['expiry_date']} | Qty: {batch['quantity']} | Outlet: {batch['outlet_name']}\n"
    
    if expiring_batches:
        response += f"\n⚠️ **EXPIRING WITHIN 30 DAYS ({len(expiring_batches)}):**\n"
        for batch in expiring_batches:
            days_left = (batch['expiry_date'] - datetime.utcnow().date()).days
            response += f"   • {batch['medicine_name']} (Batch: {batch['batch_number']})\n"
            response += f"     Expiry: {batch['expiry_date']} ({days_left} days) | Qty: {batch['quantity']} | Outlet: {batch['outlet_name']}\n"
    
    if not expired_batches and not expiring_batches:
        response += f"\n✅ No medicines expiring in the next 30 days.\n"
    
    response += f"""
{'─' * 50}
💡 **Actions Required:**
• Remove expired items immediately
• Plan promotional discounts for expiring items
• Implement FIFO (First In First Out) rotation
• Review supplier lead times
{'─' * 50}
"""
    
    return response.strip()


def format_restock_response(critical_items, high_demand_items):
    """Format restocking recommendations with priorities."""
    
    response = f"""
📦 **Restocking Recommendations**
{'─' * 50}
"""
    
    if not critical_items and not high_demand_items:
        response += f"""✅ All medicines are adequately stocked!
Current inventory levels are healthy.
{'─' * 50}
"""
        return response.strip()
    
    if critical_items:
        response += f"\n🔴 **CRITICAL - Reorder Immediately ({len(critical_items)} items):**\n"
        for med in critical_items:
            shortage = med['reorder_point'] - med['quantity']
            response += f"   • {med['name'].upper()} (Outlet: {med['outlet_name']})\n"
            response += f"     Current: {med['quantity']} | Min Level: {med['reorder_point']} | Shortage: {shortage}\n"
    
    if high_demand_items:
        response += f"\n🟡 **HIGH PRIORITY - Fast-Moving Items ({len(high_demand_items)}):**\n"
        for med in high_demand_items:
            response += f"   • {med['name'].upper()} (Outlet: {med['outlet_name']})\n"
            response += f"     Current Stock: {med['quantity']} | Monthly Demand: {med['monthly_sales']} units\n"
            response += f"     ⚡ Stock Covers: {med['stock_days']:.1f} days of sales\n"
    
    response += f"""
{'─' * 50}
💡 **Recommended Actions:**
• Contact suppliers for critical items immediately
• Prioritize by outlet location and demand
• Check supplier lead times and plan accordingly
• Monitor critical items daily
• Consider increasing safety stock for fast-moving items
{'─' * 50}
"""
    
    return response.strip()


def format_outlet_performance(outlets_data):
    """Format outlet performance comparison."""
    
    if not outlets_data:
        return "🏪 No outlet performance data available."
    
    response = f"""
🏪 **Outlet Performance Comparison**
{'─' * 50}

"""
    
    for outlet in outlets_data:
        response += f"📍 **{outlet['outlet_name'].upper()}** ({outlet['outlet_type']})\n"
        response += f"   Total Sales: {outlet['total_transactions']:,} transactions\n"
        response += f"   Revenue: ₹{outlet['revenue']:,.2f}\n"
        response += f"   Avg Transaction: ₹{outlet['avg_transaction']:,.2f}\n"
        response += f"   Stock Items: {outlet['stock_count']}\n\n"
    
    response += f"""
{'─' * 50}
💡 **Insights:**
• Compare outlet performance for best practices
• Learn from high-performing outlets
• Support underperforming outlets with inventory
• Track outlet-specific demand patterns
{'─' * 50}
"""
    
    return response.strip()


def format_margin_response(margins_data):
    """Format profit margin analysis."""
    
    response = f"""
💰 **Profitability Analysis**
{'─' * 50}

"""
    
    total_revenue = sum(m['revenue'] for m in margins_data)
    total_cost = sum(m['cost'] for m in margins_data)
    total_profit = total_revenue - total_cost
    overall_margin = ((total_profit / total_revenue) * 100) if total_revenue > 0 else 0
    
    response += f"Total Revenue: ₹{total_revenue:,.2f}\n"
    response += f"Total Cost: ₹{total_cost:,.2f}\n"
    response += f"Total Profit: ₹{total_profit:,.2f}\n"
    response += f"Overall Margin: {overall_margin:.2f}%\n\n"
    
    response += "Top Margin Items:\n"
    sorted_margins = sorted(margins_data, key=lambda x: x['margin_percent'], reverse=True)[:5]
    
    for med in sorted_margins:
        response += f"   • {med['name'].upper()}: {med['margin_percent']:.2f}% margin\n"
    
    response += f"""
{'─' * 50}
💡 **Insights:**
• Focus on high-margin items for profitability
• Review low-margin items for pricing adjustments
• Monitor cost trends
• Optimize inventory for margin optimization
{'─' * 50}
"""
    
    return response.strip()


def get_top_medicines(db, limit=5):
    """Get top selling medicines with revenue and profit."""
    try:
        results = db.query(
            Medicine.id,
            Medicine.name,
            func.sum(Sale.quantity).label('total_qty'),
            func.sum(Sale.total_price).label('revenue'),
            func.sum(Medicine.cost_price * Sale.quantity).label('cost')
        ).join(Sale, Sale.medicine_id == Medicine.id)\
         .group_by(Medicine.id, Medicine.name)\
         .order_by(func.sum(Sale.quantity).desc())\
         .limit(limit).all()
        
        medicines = []
        for med_id, name, qty, revenue, cost in results:
            revenue = float(revenue or 0)
            cost = float(cost or 0)
            medicines.append({
                'id': med_id,
                'name': name,
                'quantity': int(qty or 0),
                'revenue': revenue,
                'profit': revenue - cost
            })
        
        return medicines
    except Exception as e:
        print(f"Error in get_top_medicines: {str(e)}")
        return []


def get_expiry_data(db, days=30):
    """Get expired and expiring batches."""
    try:
        today = datetime.utcnow().date()
        cutoff_date = today + timedelta(days=days)
        
        expired = db.query(
            Medicine.name,
            Batch.batch_number,
            Batch.expiry_date,
            Batch.quantity,
            Outlet.name.label('outlet_name')
        ).join(Medicine, Batch.medicine_id == Medicine.id)\
         .join(Outlet, Batch.outlet_id == Outlet.id)\
         .filter(Batch.expiry_date <= today).all()
        
        expiring = db.query(
            Medicine.name,
            Batch.batch_number,
            Batch.expiry_date,
            Batch.quantity,
            Outlet.name.label('outlet_name')
        ).join(Medicine, Batch.medicine_id == Medicine.id)\
         .join(Outlet, Batch.outlet_id == Outlet.id)\
         .filter(
            and_(
                Batch.expiry_date > today,
                Batch.expiry_date <= cutoff_date
            )
        ).all()
        
        expired_batches = [
            {
                'medicine_name': name,
                'batch_number': batch_num,
                'expiry_date': exp_date,
                'quantity': qty,
                'outlet_name': outlet_name
            }
            for name, batch_num, exp_date, qty, outlet_name in expired
        ]
        
        expiring_batches = [
            {
                'medicine_name': name,
                'batch_number': batch_num,
                'expiry_date': exp_date,
                'quantity': qty,
                'outlet_name': outlet_name
            }
            for name, batch_num, exp_date, qty, outlet_name in expiring
        ]
        
        return expired_batches, expiring_batches
    except Exception as e:
        print(f"Error in get_expiry_data: {str(e)}")
        return [], []


def get_restock_recommendations(db, critical_threshold=50, high_demand_threshold=100):
    """
    Get medicines that need restocking based on:
    1. Low stock levels (below threshold)
    2. High demand (fast-moving items with low stock)
    """
    try:
        critical_items = []
        high_demand_items = []
        
        # Get all medicines with their current stock per outlet
        medicines = db.query(Medicine).all()
        
        for medicine in medicines:
            outlets = db.query(Outlet).all()
            
            for outlet in outlets:
                # Get current stock for this medicine at this outlet
                total_stock = db.query(func.sum(Batch.quantity)).filter(
                    and_(
                        Batch.medicine_id == medicine.id,
                        Batch.outlet_id == outlet.id
                    )
                ).scalar() or 0
                
                # Get sales in last 30 days
                last_30_days = datetime.utcnow() - timedelta(days=30)
                monthly_sales = db.query(func.sum(Sale.quantity)).filter(
                    and_(
                        Sale.medicine_id == medicine.id,
                        Sale.outlet_id == outlet.id,
                        Sale.timestamp >= last_30_days
                    )
                ).scalar() or 0
                
                # CRITICAL: Stock below threshold
                if total_stock < critical_threshold:
                    critical_items.append({
                        'id': medicine.id,
                        'name': medicine.name,
                        'quantity': int(total_stock),
                        'reorder_point': critical_threshold,
                        'outlet_id': outlet.id,
                        'outlet_name': outlet.name
                    })
                
                # HIGH PRIORITY: Fast-moving with low stock
                if monthly_sales > high_demand_threshold and total_stock < (monthly_sales / 2):
                    stock_days = (total_stock / (monthly_sales / 30)) if monthly_sales > 0 else 0
                    high_demand_items.append({
                        'id': medicine.id,
                        'name': medicine.name,
                        'quantity': int(total_stock),
                        'monthly_sales': int(monthly_sales),
                        'stock_days': stock_days,
                        'outlet_id': outlet.id,
                        'outlet_name': outlet.name
                    })
        
        return critical_items, high_demand_items
    except Exception as e:
        print(f"Error in get_restock_recommendations: {str(e)}")
        return [], []


def get_outlet_performance(db):
    """Get performance metrics for all outlets."""
    try:
        outlets = db.query(Outlet).all()
        outlets_data = []
        
        for outlet in outlets:
            total_transactions = db.query(func.count(Sale.id)).filter(
                Sale.outlet_id == outlet.id
            ).scalar() or 0
            
            revenue = db.query(func.sum(Sale.total_price)).filter(
                Sale.outlet_id == outlet.id
            ).scalar() or 0
            
            avg_transaction = (revenue / total_transactions) if total_transactions > 0 else 0
            
            stock_count = db.query(func.count(Batch.id)).filter(
                Batch.outlet_id == outlet.id
            ).scalar() or 0
            
            outlets_data.append({
                'outlet_id': outlet.id,
                'outlet_name': outlet.name,
                'outlet_type': outlet.type,
                'total_transactions': int(total_transactions),
                'revenue': float(revenue or 0),
                'avg_transaction': float(avg_transaction),
                'stock_count': int(stock_count)
            })
        
        return outlets_data
    except Exception as e:
        print(f"Error in get_outlet_performance: {str(e)}")
        return []


def get_margin_analysis(db):
    """Get profitability analysis for all medicines."""
    try:
        results = db.query(
            Medicine.id,
            Medicine.name,
            Medicine.cost_price,
            func.sum(Sale.quantity).label('total_qty'),
            func.sum(Sale.total_price).label('revenue')
        ).join(Sale, Sale.medicine_id == Medicine.id)\
         .group_by(Medicine.id, Medicine.name, Medicine.cost_price).all()
        
        margins_data = []
        for med_id, name, cost_price, qty, revenue in results:
            qty = int(qty or 0)
            revenue = float(revenue or 0)
            cost = float(cost_price * qty or 0)
            profit = revenue - cost
            margin_percent = ((profit / revenue) * 100) if revenue > 0 else 0
            
            margins_data.append({
                'id': med_id,
                'name': name,
                'quantity': qty,
                'revenue': revenue,
                'cost': cost,
                'profit': profit,
                'margin_percent': margin_percent
            })
        
        return margins_data
    except Exception as e:
        print(f"Error in get_margin_analysis: {str(e)}")
        return []


def process_query(user_query):
    """
    Enhanced query processor with comprehensive pharmacy analytics.
    Uses intent detection, context-aware queries, and rich formatting.
    """
    db = SessionLocal()
    
    try:
        query_lower = user_query.lower()
        
        # Detect intent with confidence
        intent, confidence = detect_intent(query_lower)
        
        # 🧠 RULE ENGINE - High confidence responses
        
        if intent == "revenue" and confidence >= 0.85:
            revenue = db.query(func.sum(Sale.total_price)).scalar()
            outlet_count = db.query(func.count(Outlet.id)).scalar() or 0
            response = format_revenue_response(revenue, outlet_count)
            db.close()
            return response
        
        if intent == "sales_count" and confidence >= 0.85:
            count = db.query(func.count(Sale.id)).scalar()
            outlet_count = db.query(func.count(Outlet.id)).scalar() or 0
            response = format_sales_response(count, outlet_count)
            db.close()
            return response
        
        if intent == "top_medicine" and confidence >= 0.85:
            medicines = get_top_medicines(db)
            response = format_top_medicine_response(medicines)
            db.close()
            return response
        
        if intent == "expiry" and confidence >= 0.85:
            expired, expiring = get_expiry_data(db)
            response = format_expiry_response(expired, expiring)
            db.close()
            return response
        
        if intent == "restock" and confidence >= 0.85:
            critical, high_demand = get_restock_recommendations(db)
            response = format_restock_response(critical, high_demand)
            db.close()
            return response
        
        if intent == "outlet_performance" and confidence >= 0.85:
            outlets_data = get_outlet_performance(db)
            response = format_outlet_performance(outlets_data)
            db.close()
            return response
        
        if intent == "margin" and confidence >= 0.85:
            margins_data = get_margin_analysis(db)
            response = format_margin_response(margins_data)
            db.close()
            return response
        
        # 🤖 LLM FALLBACK - For low confidence or unknown intents
        
        prompt = f"""
You are a pharmacy operations assistant for Meds Pharmacy Platform.

User Question: {user_query}

You have access to:
- Sales transactions and revenue data
- Medicine inventory and batch tracking
- Multi-outlet operations (18 pharmacy stores + 1 warehouse)
- Pricing and profitability data
- Stock levels and expiry dates

Provide:
- Clear, actionable insights for pharmacy managers
- Business metrics with specific numbers
- Practical recommendations
- Professional, simple language

Guidelines:
- If asked about revenue, sales, medicines, stock, expiry, restocking, outlets, or margins - provide insights
- Keep responses concise (5-8 sentences max)
- Always include specific recommendations
- Use business metrics where relevant
- Suggest next steps or actions

Provide a helpful response that a pharmacy manager would find useful.
        """
        
        try:
            llm_response = query_llm(prompt)
            
            if llm_response:
                response = f"""
🤖 **AI Assistant Response**
{'─' * 50}
{llm_response.strip()}
{'─' * 50}
                """
                db.close()
                return response.strip()
            else:
                db.close()
                return "❌ Unable to generate response. Please try again."
        
        except Exception as e:
            db.close()
            return f"""
⚠️ **Service Unavailable**
{'─' * 50}
The AI service is temporarily unavailable.

Try asking about:
• Total revenue & sales
• Top selling medicines
• Expiring stock & batch tracking
• Restocking recommendations
• Outlet performance comparison
• Profit margins & profitability

Or contact support if the issue persists.
{'─' * 50}
            """.strip()
    
    except Exception as e:
        print(f"Error in process_query: {str(e)}")
        db.close()
        return f"❌ Error processing query: {str(e)}\n\nPlease try again with a different question."