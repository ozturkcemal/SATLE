import csv
from bs4 import BeautifulSoup

def parse_mtu_timetable(html_file, output_file):
    with open(html_file, 'r', encoding='ISO-8859-1') as f:
        soup = BeautifulSoup(f, 'lxml')

    # Mapping day names to their starting hour offset
    DAY_MAP = {
        'Mon': 0.0,
        'Tue': 9.0,
        'Wed': 18.0,
        'Thu': 27.0,
        'Fri': 36.0
    }

    records = []

    # Find all tables that represent a timetable grid
    # We look for tables with a border='1' and specific spacing
    timetable_grids = soup.find_all('table', {'cellspacing': '0', 'border': '1'})

    for grid in timetable_grids:
        # 1. Extract Metadata (Class and Dept)
        class_group = "Unknown"
        dept = "Unknown"
        header_area = grid.find_previous(lambda tag: tag.name == 'table' and "Class:" in tag.get_text())
        
        if header_area:
            header_text = header_area.get_text(" ", strip=True)
            try:
                if "Class:" in header_text:
                    class_group = header_text.split("Class:")[1].split("Department")[0].strip()
                if "Department" in header_text:
                    dept = header_text.split("Department")[1].split("Contact")[0].strip()
            except Exception:
                pass

        # 2. Parse Rows
        rows = grid.find_all('tr', recursive=False)
        
        for row in rows:
            cells = row.find_all('td', recursive=False)
            if not cells:
                continue
            
            # Identify the day from the first cell
            day_label = cells[0].get_text(strip=True)
            if day_label not in DAY_MAP:
                continue  # Skip header rows or spacer rows
            
            day_offset = DAY_MAP[day_label]
            column_offset = 0.0 
            
            # Process session cells (skip the day label cell itself)
            for cell in cells[1:]:
                colspan = int(cell.get('colspan', 1))
                duration = colspan * 0.25 # 15 mins = 0.25 hours
                
                inner_tables = cell.find_all('table')
                if inner_tables:
                    # Extract Data
                    t1_cols = inner_tables[0].find_all('td')
                    module = t1_cols[0].get_text(strip=True) if t1_cols else ""
                    act_type = t1_cols[1].get_text(strip=True) if len(t1_cols) > 1 else ""
                    lecturer = inner_tables[1].get_text(strip=True) if len(inner_tables) > 1 else ""
                    
                    room, weeks = "", ""
                    if len(inner_tables) > 2:
                        t3_cols = inner_tables[2].find_all('td')
                        room = t3_cols[0].get_text(strip=True) if t3_cols else ""
                        weeks = t3_cols[1].get_text(strip=True) if len(t3_cols) > 1 else ""
                    
                    # Calculate final timeslot
                    timeslot = day_offset + column_offset

                    records.append({
                        'Timeslot': timeslot,
                        'Lecturer': lecturer,
                        'Module': module,
                        'Dept': dept,
                        'ClassGroups': class_group,
                        'ActType': act_type,
                        'Weeks': weeks,
                        'Duration': duration,
                        'Room': room
                    })
                
                # Always increment column offset by cell width
                column_offset += duration

    # 3. Sort by Timeslot and re-index Idx
    records.sort(key=lambda x: (x['Timeslot'], x['ClassGroups']))
    for idx, record in enumerate(records):
        record['Idx'] = idx

    # 4. Save
    fieldnames = ['Idx', 'Timeslot', 'Lecturer', 'Module', 'Dept', 'ClassGroups', 'ActType', 'Weeks', 'Duration', 'Room']
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(records)

# Execution
parse_mtu_timetable('Parser/Sem1_All_StudentSets.htm', 'csStdGrpsParsed_FINAL.tsv')
print("Fixed parsing complete. Max timeslot should now be < 45.0")