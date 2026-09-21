import re
import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.inventory import ToolInventory

def parse_inventory(text):
    lines = [l for l in text.splitlines() if l.strip()]
    tools = []
    for line in lines:
        parts = re.split(r'\t| {2,}', line)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) < 3:
            continue
        tool = dict(
            name=parts[1] if len(parts) > 1 else '',
            range_mm=parts[2] if len(parts) > 2 else '',
            identification_code=parts[3] if len(parts) > 3 else '',
            make=parts[4] if len(parts) > 4 else '',
            quantity=parts[5] if len(parts) > 5 else '',
            location=parts[6] if len(parts) > 6 else '',
            gauge=parts[7] if len(parts) > 7 else '',
            remarks=parts[8] if len(parts) > 8 else ''
        )
        try:
            tool['quantity'] = int(re.sub(r'[^0-9]', '', tool['quantity']))
        except Exception:
            tool['quantity'] = 0
        tools.append(tool)
    return tools

def import_tools(text):
    db: Session = SessionLocal()
    tools = parse_inventory(text)
    for t in tools:
        tool_name = t['name']
        if not tool_name:
            continue
        try:
            existing = db.query(ToolInventory).filter(ToolInventory.tool_name == tool_name).first()
            if existing:
                existing.quantity = t['quantity']
                existing.range_mm = t['range_mm']
                existing.identification_code = t['identification_code']
                existing.make = t['make']
                existing.location = t['location']
                existing.gauge = t['gauge']
                existing.remarks = t['remarks']
            else:
                tool_obj = ToolInventory(
                    tool_name=tool_name,
                    quantity=t['quantity'],
                    range_mm=t['range_mm'],
                    identification_code=t['identification_code'],
                    make=t['make'],
                    location=t['location'],
                    gauge=t['gauge'],
                    remarks=t['remarks']
                )
                db.add(tool_obj)
        except Exception as e:
            print(f"Error processing {tool_name}: {e}")
    try:
        db.commit()
        print(f"Imported {len(tools)} tools.")
    except Exception as e:
        print(f"Commit failed: {e}")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        print("Paste your inventory text, then press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) and Enter:")
        text = sys.stdin.read()
    import_tools(text)
