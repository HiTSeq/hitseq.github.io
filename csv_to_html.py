#!/usr/bin/env python3
import argparse
import csv
from datetime import datetime
from collections import defaultdict

def format_time(time_str):
    # time_str is typically HH:MM:SS
    # We want HH:MM
    parts = time_str.split(":")
    if len(parts) >= 2:
        return f"{parts[0]}:{parts[1]}"
    return time_str

def format_date(date_str):
    # date_str is YYYY-MM-DD
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        # Format: Monday, July 13, 2026
        return dt.strftime("%A, %B %d, %Y")
    except ValueError:
        return date_str


def find_presenter_in_authors(presenter, authors_list):
    p_clean = presenter.strip().lower()
    for idx, author in enumerate(authors_list):
        if author.strip().lower() == p_clean:
            return idx
            
    best_idx = -1
    best_ratio = 0.0
    for idx, author in enumerate(authors_list):
        a_clean = author.strip().lower()
        import difflib
        ratio = difflib.SequenceMatcher(None, p_clean, a_clean).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = idx
            
    if best_ratio >= 0.8:
        return best_idx
        
    return -1

def convert_csv_to_html(csv_path, html_path, timezone="EST"):
    rows_by_date = defaultdict(list)
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        # DictReader uses the first line as fieldnames
        reader = csv.DictReader(f)
        
        # Strip header names in case of leading/trailing spaces
        reader.fieldnames = [name.strip() for name in reader.fieldnames] if reader.fieldnames else []
        
        # Find exact field name mappings (handling typos like "Confrimed Presenter")
        field_map = {}
        for name in reader.fieldnames:
            norm_name = name.lower().replace(" ", "").replace("_", "")
            field_map[norm_name] = name
            
        for row in reader:
            date_field = field_map.get("date", "Date")
            date_val = row.get(date_field)
            if date_val:
                rows_by_date[date_val].append(row)
            
    # Sort the dates
    sorted_dates = sorted(rows_by_date.keys())
    
    html_lines = []
    
    for i, date_val in enumerate(sorted_dates):
        day_rows = rows_by_date[date_val]
        if not day_rows:
            continue
            
        # Get room of the first entry for this date
        first_row = day_rows[0]
        room_field = field_map.get("room", "Room")
        room_val = first_row.get(room_field, "").strip()
        
        formatted_date = format_date(date_val)
        
        # Add date header
        html_lines.append(f"<h3>{formatted_date}</h3>\n\n")
        html_lines.append(f"<p>All times listed are in {timezone}, Room: {room_val}</p>\n\n")
        
        # Start table
        html_lines.append('<table style="width: 100%;" border="0">\n')
        html_lines.append('<tbody>\n')
        
        for row in day_rows:
            # Extract fields using normalized mapping
            title = row.get(field_map.get("title", "Title"), "").strip()
            start_time = row.get(field_map.get("starttime", "Start Time"), "").strip()
            end_time = row.get(field_map.get("endtime", "End Time"), "").strip()
            
            # Keynote speaker name might be in "Authors" or "Confrimed Presenter"
            # Support both "Confrimed Presenter" (original typo) and corrected "Confirmed Presenter"
            presenter_key = field_map.get("confrimedpresenter") or field_map.get("confirmedpresenter") or "Confrimed Presenter"
            presenter = row.get(presenter_key, "").strip()
            
            authors = row.get(field_map.get("authors", "Authors"), "").strip()
            format_val = row.get(field_map.get("format", "Format"), "").strip()
            abstract = row.get(field_map.get("abstract", "Abstract"), "").strip()
            
            time_range = f"{format_time(start_time)}-{format_time(end_time)}"
            
            # Parse authors list
            authors_list = [a.strip() for a in authors.split(",") if a.strip()]
            if presenter:
                idx = find_presenter_in_authors(presenter, authors_list)
                if idx != -1:
                    authors_list[idx] = f"<strong>{authors_list[idx]}</strong>"
                else:
                    if authors_list:
                        authors_list.append(f"<strong>{presenter}</strong>")
                    else:
                        authors_list = [f"<strong>{presenter}</strong>"]
            
            formatted_authors = ", ".join(authors_list)

            # Style classification
            if title.lower() == "welcome":
                content = f"<strong>{title}</strong>"
            elif title.lower() == "tbd":
                # Invited Presentation
                pres_name = presenter if presenter else authors
                if pres_name:
                    content = f"<strong>Invited Presentation:</strong> {title}<br/><strong>{pres_name}</strong>"
                else:
                    content = f"<strong>Invited Presentation:</strong> {title}"
            else:
                # Regular or Proceedings presentation
                # If abstract starts with "Motivation:", it is a Proceedings Presentation
                is_proceedings = abstract.startswith("Motivation:") or "\nMotivation:" in abstract
                prefix = "Proceedings Presentation: " if is_proceedings else ""
                
                if formatted_authors:
                    content = f"{prefix}{title}<br/>{formatted_authors}"
                else:
                    content = f"{prefix}{title}"
                
            # Build the row HTML
            row_html = (
                "<tr>\n"
                f' <td style="vertical-align: top;"><strong>{time_range}</strong></td>\n'
                f' <td style="vertical-align: top;">{content}</td>\n'
                "</tr>\n"
            )
            html_lines.append(row_html)
            
        html_lines.append('</tbody>\n')
        html_lines.append('</table>\n')
        
        # Add spacing between tables unless it is the last table
        if i < len(sorted_dates) - 1:
            html_lines.append('\n')
            
    # Write to output file
    with open(html_path, mode='w', encoding='utf-8') as f:
        f.writelines(html_lines)

def main():
    parser = argparse.ArgumentParser(description="Convert HiTSeq schedule CSV to HTML table.")
    parser.add_argument("--csv", required=True, help="Path to input CSV file.")
    parser.add_argument("--out", required=True, help="Path to output HTML file.")
    parser.add_argument("--timezone", default="EST", help="Timezone to display in HTML (default: EST).")
    args = parser.parse_args()
    
    convert_csv_to_html(args.csv, args.out, args.timezone)
    print(f"Successfully converted {args.csv} to {args.out}")

if __name__ == "__main__":
    main()
