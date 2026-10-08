import reflex as rx
import pandas as pd
import io
import re

class State(rx.State):
    """Manages the uploaded Excel data and filters it based on text commands."""
    data: list[dict] = []
    columns: list[str] = []
    filtered_data: list[dict] = []
    command: str = ""
    message: str = ""

    def update_command(self, val: str):
        """Saves the text you type into the command search bar."""
        self.command = val

    async def handle_upload(self, files: list[rx.UploadFile]):
        """Reads your uploaded student Excel spreadsheet data."""
        if not files:
            self.message = "No file selected."
            return
        
        file = files
        upload_data = await file.read()
        
        try:
            df = pd.read_excel(io.BytesIO(upload_data))
            # Clean up headers to lowercase so spacing/caps don't break things
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            self.columns = list(df.columns)
            self.data = df.to_dict(orient="records")
            self.filtered_data = self.data
            self.message = f"Successfully loaded {len(df)} student records!"
        except Exception as e:
            self.message = f"Error reading file: {str(e)}"

    def parse_and_filter(self):
        """Filters rows dynamically based on keywords like cgpa, attendance, or backlog."""
        if not self.data:
            self.message = "Please upload an Excel sheet first."
            return
        
        cmd = self.command.lower().strip()
        df = pd.DataFrame(self.data)
        
        try:
            # 1. Check for CGPA criteria
            cgpa_col = next((col for col in df.columns if "cgpa" in col), None)
            if cgpa_col:
                df[cgpa_col] = pd.to_numeric(df[cgpa_col], errors="coerce")
                less_match = re.search(r"less than\s+([0-9.]+)", cmd)
                more_match = re.search(r"more than\s+([0-9.]+)", cmd)
                
                if "cgpa" in cmd:
                    if less_match:
                        df = df[df[cgpa_col] < float(less_match.group(1))]
                    elif more_match:
                        df = df[df[cgpa_col] > float(more_match.group(1))]

            # 2. Check for Attendance criteria
            attend_col = next((col for col in df.columns if "attend" in col), None)
            if attend_col:
                df[attend_col] = pd.to_numeric(df[attend_col], errors="coerce")
                less_match = re.search(r"less than\s+([0-9.]+)", cmd)
                more_match = re.search(r"more than\s+([0-9.]+)", cmd)
                
                if "attend" in cmd:
                    if less_match:
                        df = df[df[attend_col] < float(less_match.group(1))]
                    elif more_match:
                        df = df[df[attend_col] > float(more_match.group(1))]

            # 3. Check for Backlog criteria
            backlog_col = next((col for col in df.columns if "backlog" in col), None)
            if backlog_col:
                df[backlog_col] = pd.to_numeric(df[backlog_col], errors="coerce")
                backlog_match = re.search(r"with\s+(\d+)\s+backlog", cmd)
                if backlog_match:
                    df = df[df[backlog_col] == int(backlog_match.group(1))]
            
            self.filtered_data = df.to_dict(orient="records")
            self.message = f"Found {len(df)} matching records."
            
        except Exception as e:
            self.message = f"Error executing command: {str(e)}"

def index() -> rx.Component:
    """Builds the actual frontend user dashboard interface page."""
    return rx.center(
        rx.vstack(
            rx.heading("Student Data Analyzer Dashboard", size="7", margin_bottom="1em"),
            
            # File Upload Drag-and-Drop View
            rx.vstack(
                rx.upload(
                    rx.text("Drag & Drop your Excel sheet here or Click to Browse"),
                    border="2px dashed #cccccc",
                    padding="2em",
                    border_radius="8px",
                    id="excel_upload"
                ),
                rx.button(
                    "Upload Sheet",
                    on_click=State.handle_upload(rx.upload_files(upload_id="excel_upload")),
                    color_scheme="blue"
                ),
                align="center",
                spacing="3"
            ),
            
            # Search / Natural Language prompt bar
            rx.hstack(
                rx.input(
                    placeholder="e.g., attendance less than 75 / less than 7 cgpa",
                    on_change=State.update_command,
                    width="400px"
                ),
                rx.button("Analyze & Filter", on_click=State.parse_and_filter, color_scheme="green"),
                margin_top="1.5em",
                spacing="3"
            ),
            
            # Status alerts text
            rx.cond(
                State.message != "",
                rx.text(State.message, font_weight="bold", color="blue", margin_top="1em")
            ),
            
            # Dynamic Spreadsheet Results Grid
            rx.cond(
                State.filtered_data,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(State.columns, lambda col: rx.table.column_header_cell(col.upper()))
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            State.filtered_data,
                            lambda row: rx.table.row(
                                rx.foreach(State.columns, lambda col: rx.table.cell(row[col].to_string()))
                            )
                        )
                    ),
                    width="100%",
                    margin_top="2em"
                ),
                rx.text("No data loaded.", margin_top="2em", color="gray")
            ),
            
            width="80%",
            max_width="1000px",
            padding="2em",
            align="center"
        ),
        width="100vw",
        min_height="100vh",
        background_color="#f9f9fb"
    )

app = rx.App()
app.add_page(index)