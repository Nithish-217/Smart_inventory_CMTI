from app.db.session import get_db
from app.models.inventory import ToolInventory

def seed_tools():
    db = next(get_db())
    tools = [
        ToolInventory(tool_name="Vernier Caliper", make="Mitutoyo", range_mm="150", quantity=10),
        ToolInventory(tool_name="Micrometer", make="Starrett", range_mm="25", quantity=5),
        ToolInventory(tool_name="Dial Gauge", make="Baker", range_mm="10", quantity=8),
        ToolInventory(tool_name="Height Gauge", make="Mitutoyo", range_mm="300", quantity=3),
    ]
    for tool in tools:
        db.add(tool)
    db.commit()
    print("Seeded sample tools.")

if __name__ == "__main__":
    seed_tools()
