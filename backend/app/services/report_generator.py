import os
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import urllib.request

class PDFReportGenerator:
    def __init__(self):
        self.reports_dir = os.path.join(os.getcwd(), "reports")
        self.fonts_dir = os.path.join(os.getcwd(), "fonts")
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.fonts_dir, exist_ok=True)
        
    def _get_font(self, font_name: str, url: str) -> str:
        filepath = os.path.join(self.fonts_dir, f"{font_name}.ttf")
        if not os.path.exists(filepath):
            try:
                urllib.request.urlretrieve(url, filepath)
            except Exception:
                pass # fallback to basic later
        return filepath
        
    def _generate_activity_chart(self, trend_dict: dict, save_path: str):
        plt.figure(figsize=(8, 4))
        plt.plot(list(trend_dict.keys()), list(trend_dict.values()), marker='o', color='#6b4cff', linewidth=2)
        plt.title('Commit Activity Over Time')
        plt.xlabel('Month')
        plt.ylabel('Commits')
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(save_path, format='png', dpi=150)
        plt.close()
        
    def _generate_intent_chart(self, nlp_breakdown: dict, save_path: str):
        labels = list(nlp_breakdown.keys())
        sizes = list(nlp_breakdown.values())
        
        # Filter out 0 size slices
        labels = [l for i, l in enumerate(labels) if sizes[i] > 0]
        sizes = [s for s in sizes if s > 0]
        
        if not sizes:
            sizes = [1]
            labels = ["Unknown"]
            
        plt.figure(figsize=(6, 6))
        colors = ['#00e676', '#ff5252', '#ffab40', '#42a5f5', '#9e9e9e']
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
        plt.title('Semantic Commit Intent Analysis')
        plt.tight_layout()
        plt.savefig(save_path, format='png', dpi=150)
        plt.close()
        
    def generate_report(self, repo_name: str, metrics: dict, reasoning: dict, nlp_data: dict, decay_data: dict, language: str = "English") -> str:
        pdf = FPDF()
        pdf.add_page()
        
        # Determine Font based on language
        font_family = "Helvetica" # Default
        font_url = None
        font_file = None
        
        if language in ["Turkish", "German", "Spanish", "French", "Russian", "Italian"]:
            # Download DejaVuSans which supports Cyrillic and extensive Latin
            font_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
            font_family = "DejaVu"
            font_file = "DejaVuSans"
        elif language in ["Chinese", "Japanese"]:
            try:
                # GitHub allows access to raw fonts for Noto CJK
                font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
                font_family = "NotoCJK"
                font_file = "NotoSansCJKsc-Regular"
            except Exception:
                pass
        elif language == "Arabic":
            font_url = "https://github.com/google/fonts/raw/main/ofl/notosansarabic/NotoSansArabic%5Bwdth%2Cwght%5D.ttf"
            font_family = "NotoArabic"
            font_file = "NotoSansArabic"
            pdf.set_text_shaping(True)
            
        try:
            # If standard linux DejaVu exists, map directly
            if font_family == "DejaVu" and os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
            elif font_url:
                local_font = self._get_font(font_file, font_url)
                if os.path.exists(local_font):
                    pdf.add_font(font_family, "", local_font, uni=True)
        except Exception as e:
            # Fail silently, fallback to Helvetica
            font_family = "Helvetica"
            
        # Title Section
        pdf.set_fill_color(30, 30, 40)
        pdf.set_text_color(255, 255, 255)
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 24)
        else:
            pdf.set_font("Helvetica", "B", 24)
            
        pdf.cell(0, 15, " GitDeep Archaeology Report", ln=True, align='L', fill=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 16)
        else:
            pdf.set_font("Helvetica", "B", 16)
            
        pdf.cell(0, 10, f"Target Repository: {repo_name}", ln=True, align='L')
        
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 10)
        else:
            pdf.set_font("Helvetica", "", 10)
            
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='L')
        pdf.cell(0, 8, f"Report Language: {language}", ln=True, align='L')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Status Box
        pdf.set_font("Helvetica", "B", 14)
        
        # Color code based on status
        status = reasoning['status']
        if "Critical" in status or "Danger" in status:
            pdf.set_fill_color(255, 200, 200) # Light Red
        elif "Warning" in status or "Risk" in status or "At Risk" in status:
            pdf.set_fill_color(255, 230, 180) # Light Orange
        else:
            pdf.set_fill_color(200, 255, 200) # Light Green
            
        pdf.cell(0, 12, f" Archeological Status: {status} (Score: {reasoning['health_score']}/100)", ln=True, fill=True)
        pdf.ln(8)
        
        # Summary
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 12)
        else:
            pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 8, reasoning['summary'])
        pdf.ln(8)
        
        # Divider
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Key Findings
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(40, 40, 100)
        pdf.cell(0, 10, "Key AI Findings", ln=True)
        pdf.set_text_color(0, 0, 0)
        
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 12)
        else:
            pdf.set_font("Helvetica", "", 12)
            
        for reason in reasoning['reasons']:
            pdf.set_x(15) # Indent
            pdf.multi_cell(0, 8, f"- {reason}")
            pdf.ln(2)
            
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Raw Metrics Snapshot
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(40, 40, 100)
        pdf.cell(0, 10, "Core Technical Snapshot", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 11)
        
        # Create a tiny 2-column layout for metrics
        pdf.set_x(15)
        col1_x = pdf.get_x()
        metrics_y = pdf.get_y()
        
        pdf.cell(80, 8, f"- Analyzed Commits: {metrics.get('commits_analyzed', 0)}", ln=True)
        pdf.set_x(15)
        pdf.cell(80, 8, f"- Stars / Issues: {metrics.get('stars', 0)} / {metrics.get('open_issues', 0)}", ln=True)
        pdf.set_x(15)
        pdf.cell(80, 8, f"- Bus Factor Risk: {metrics.get('bus_factor', 0)}", ln=True)
        
        pdf.set_xy(col1_x + 90, metrics_y)
        pdf.cell(80, 8, f"- 12m Stagnation: {'Yes (At Risk)' if metrics.get('is_stagnant') else 'Active'}", ln=True)
        pdf.set_x(col1_x + 90)
        pdf.cell(80, 8, f"- Tech Debt Ratio: {metrics.get('tech_debt_ratio', 0)}", ln=True)
        pdf.set_x(col1_x + 90)
        
        # Add total files if available
        fm = metrics.get('file_metrics', {})
        total_files = fm.get('total_files_tracked', 0)
        if total_files > 0:
            pdf.cell(80, 8, f"- Tracked Files: {total_files}", ln=True)
        else:
            pdf.ln(8)
            
        pdf.ln(10)
        
        # ---- NEW: File Level Analytics ----
        if fm and total_files > 0:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_text_color(40, 100, 40)
            pdf.set_fill_color(240, 250, 240)
            pdf.cell(0, 12, " File-Level Analytics & Health", ln=True, fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(8)
            
            # Hotspots
            hotspots = fm.get('hotspots', [])
            if hotspots:
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(220, 80, 80) # Red-ish
                pdf.cell(0, 8, "Top Refactoring Hotspots (Most Changed)", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 11)
                for h in hotspots[:3]:
                    pdf.set_x(15)
                    pdf.cell(0, 7, f"- {h['filename']} ({h['changes']} changes in {h['commit_count']} commits)", ln=True)
                pdf.ln(5)
                
            # Ownership Risks (Bus Factor)
            bus_risks = fm.get('ownership_risks', [])
            if bus_risks:
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(180, 40, 40) # Dark red
                pdf.cell(0, 8, "Single-Owner Dependencies (Bus Factor Risk)", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 11)
                for br in bus_risks[:3]:
                    pdf.set_x(15)
                    pdf.cell(0, 7, f"- {br['filename']} (Owner: {br['primary_owner']}, {br['ownership_pct']:.1f}% of changes)", ln=True)
                pdf.ln(5)
                
            # Inflation Risks (Bloating)
            inflation_risks = fm.get('inflation_risks', [])
            if inflation_risks:
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(200, 100, 150) # Pinkish purple
                pdf.cell(0, 8, "Technical Debt (High net line growth, low deletion)", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 11)
                for ir in inflation_risks[:3]:
                    pdf.set_x(15)
                    pdf.cell(0, 7, f"- {ir['filename']} (Added: +{ir['added']}, Deleted: -{ir['deleted']}, Net: {ir['net_growth']})", ln=True)
                pdf.ln(5)
                
            # Bug Prone
            bug_prone = fm.get('bug_prone', [])
            if bug_prone:
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(220, 150, 40) # Orange-ish
                pdf.cell(0, 8, "High-Frequency Micro-Updates (Bug Prone)", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 11)
                for b in bug_prone[:3]:
                    pdf.set_x(15)
                    pdf.cell(0, 7, f"- {b['filename']} ({b['commit_count']} commits, {b['changes']} total lines changed)", ln=True)
                pdf.ln(5)
                
            # Coupled Files
            top_coupled = fm.get('top_coupled', [])
            if top_coupled:
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(80, 80, 180) # Blue
                pdf.cell(0, 8, "Highly Coupled Files (Edited together frequently)", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 11)
                for tc in top_coupled[:3]:
                    pdf.set_x(15)
                    pdf.cell(0, 7, f"- {tc['file1']} <-> {tc['file2']} (Co-committed {tc['co_commits']} times)", ln=True)
                pdf.ln(5)
                
            # Legacy
            legacy = fm.get('legacy_candidates', [])
            if legacy:
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(100, 100, 150) # Blue-grey
                pdf.cell(0, 8, "Legacy/Stagnant Files (Touched long ago)", ln=True)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 11)
                for l in legacy[:3]:
                    pdf.set_x(15)
                    # Format last_seen date nicely
                    date_str = l['last_seen']
                    try:
                        date_str = datetime.fromisoformat(date_str).strftime('%Y-%m-%d')
                    except:
                        pass
                    pdf.cell(0, 7, f"- {l['filename']} (Last updated: {date_str})", ln=True)
                pdf.ln(5)
                
        # Save Name & temp charts
        safe_name = repo_name.replace("/", "_")
        activity_chart_path = os.path.join(self.reports_dir, f"{safe_name}_activity.png")
        intent_chart_path = os.path.join(self.reports_dir, f"{safe_name}_intent.png")
        
        # Charts Section
        has_activity = bool(decay_data.get('activity_trend'))
        has_intent = bool(nlp_data.get('raw_breakdown'))
        
        if has_activity or has_intent:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_fill_color(240, 240, 250)
            pdf.cell(0, 12, " Visual Data Analysis", ln=True, fill=True)
            pdf.ln(10)
            
            if has_activity:
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, "Activity Trend Graph", ln=True)
                self._generate_activity_chart(decay_data['activity_trend'], activity_chart_path)
                pdf.image(activity_chart_path, x=15, w=170)
                pdf.ln(10) # extra space after image, image doesn't auto-advance Y properly sometimes
                
                # Check space for next image
                if pdf.get_y() > 150:
                    pdf.add_page()
                else:
                    pdf.set_y(pdf.get_y() + 80) # rough estimate of height
                
            if has_intent:
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, "Development Focus Breakdown", ln=True)
                self._generate_intent_chart(nlp_data['raw_breakdown'], intent_chart_path)
                # Center the pie chart roughly
                pdf.image(intent_chart_path, x=45, w=110)
            
        pdf.add_page()
        pdf.ln(15)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, "Generated by GitDeep | AI Software Archaeology Engine", ln=True, align='C')
        pdf.cell(0, 5, "Beta Forevers", ln=True, align='C')
        
        # Save PDF
        safe_name = repo_name.replace("/", "_")
        filename = f"{safe_name}_report.pdf"
        filepath = os.path.join(self.reports_dir, filename)
        
        pdf.output(filepath)
        
        # Cleanup temp charts
        if os.path.exists(activity_chart_path):
            os.remove(activity_chart_path)
        if os.path.exists(intent_chart_path):
            os.remove(intent_chart_path)
        
        return filepath
