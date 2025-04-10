from difflib import SequenceMatcher

KNOWLEDGE_BASE = [
    {"id": 1, "title": "Resetting your password", "content": "Instructions to reset your account password..."},
    {"id": 2, "title": "Connecting to company VPN", "content": "To access internal resources, use the VPN client..."},
    {"id": 3, "title": "Email configuration guide", "content": "Steps to configure your email on Outlook..."},
    {"id": 4, "title": "Troubleshooting slow internet", "content": "Check your connection, then restart router..."},
    {"id": 5, "title": "Remote desktop setup", "content": "Use RDP or TeamViewer to connect remotely..."},
]

def search_knowledge_base(query: str) -> dict:
    """
    Searches the knowledge base for the top 3 most relevant documents based on query similarity.

    Args:
        query (str): User's search input

    Returns:
        dict: Top 3 results with confidence scores, or error message
    """
    try:
        scored_results = []

        for doc in KNOWLEDGE_BASE:
            title_score = SequenceMatcher(None, query.lower(), doc["title"].lower()).ratio()
            content_score = SequenceMatcher(None, query.lower(), doc["content"].lower()).ratio()
            score = max(title_score, content_score)
            scored_results.append((score, doc))

        top_results = sorted(scored_results, key=lambda x: x[0], reverse=True)[:3]
        
        return {
            "status": "success",
            "results": [
                {
                    "id": doc["id"],
                    "title": doc["title"],
                    "confidence": round(score, 2),
                    "excerpt": doc["content"][:100] + "..."
                } for score, doc in top_results if score > 0.1
            ]
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def calculate_reimbursement(items: list) -> dict:
    """
    Calculate total reimbursement from a list of expenses.
    
    Each item in the list should be a dictionary with:
        - 'amount': float (e.g., 100.50)
        - 'category': str (optional, e.g., 'travel', 'food')
        - 'tax_deductible': bool (optional, default False)

    Example input:
    [
        {"amount": 120.00, "category": "hotel", "tax_deductible": True},
        {"amount": 50.25, "category": "meal"},
        {"amount": 300.00, "category": "flight", "tax_deductible": True}
    ]
    
    Returns:
        dict: status, total amount, total deductible, and item breakdown
    """
    try:
        total = 0
        deductible = 0
        breakdown = []

        for item in items:
            amount = float(item.get("amount", 0))
            is_deductible = item.get("tax_deductible", False)
            total += amount
            if is_deductible:
                deductible += amount
            breakdown.append({
                "category": item.get("category", "uncategorized"),
                "amount": amount,
                "deductible": is_deductible
            })

        return {
            "status": "success",
            "total_reimbursement": round(total, 2),
            "total_tax_deductible": round(deductible, 2),
            "details": breakdown
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}