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
            
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 24)
        else:
            pdf.set_font("Helvetica", "B", 24)
            
        pdf.cell(0, 10, "GitDeep Archaeology Report", ln=True, align='C')
        pdf.ln(10)
        
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 16)
        else:
            pdf.set_font("Helvetica", "B", 16)
            
        pdf.cell(0, 10, f"Target Repository: {repo_name}", ln=True, align='L')
        
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 10)
        else:
            pdf.set_font("Helvetica", "", 10)
            
        pdf.cell(0, 10, f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='L')
        pdf.cell(0, 10, f"Report Language: {language}", ln=True, align='L')
        pdf.ln(5)
        
        # Status Box
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, f" Archeological Status: {reasoning['status']} (Score: {reasoning['health_score']}/100)", ln=True, fill=True)
        pdf.ln(5)
        
        # Summary
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 12)
        else:
            pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 10, reasoning['summary'])
        pdf.ln(10)
        
        # Key Findings
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Key Findings", ln=True)
        if font_family != "Helvetica":
            pdf.set_font(font_family, "", 12)
        else:
            pdf.set_font("Helvetica", "", 12)
        for reason in reasoning['reasons']:
            pdf.multi_cell(0, 8, f"- {reason}")
            pdf.ln(2)
            
        pdf.ln(10)
        
        # Raw Metrics Data
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "Raw Technical Metrics Snapshot", ln=True)
        pdf.set_font("Helvetica", "", 11)
        
        raw_text = [
            f"Analyzed Commits: {metrics.get('commits_analyzed', 0)}",
            f"Stars: {metrics.get('stars', 0)}",
            f"Open Issues: {metrics.get('open_issues', 0)}",
            f"Bus Factor: {metrics.get('bus_factor', 0)}",
            f"Stagnant (12m Decay): {'Yes' if metrics.get('is_stagnant') else 'No'}",
            f"Tech Debt Ratio (Fixes vs Features): {metrics.get('tech_debt_ratio', 0)}"
        ]
        
        for rt in raw_text:
            pdf.cell(0, 8, f"  * {rt}", ln=True)
            
        pdf.ln(10)
        
        # Save Name & temp charts
        safe_name = repo_name.replace("/", "_")
        activity_chart_path = os.path.join(self.reports_dir, f"{safe_name}_activity.png")
        intent_chart_path = os.path.join(self.reports_dir, f"{safe_name}_intent.png")
        
        # Charts Section
        if decay_data.get('activity_trend'):
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Activity Trend Graph", ln=True)
            self._generate_activity_chart(decay_data['activity_trend'], activity_chart_path)
            pdf.image(activity_chart_path, x=10, w=180)
            pdf.ln(5)
            
        if nlp_data.get('raw_breakdown'):
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Development Focus Breakdown", ln=True)
            self._generate_intent_chart(nlp_data['raw_breakdown'], intent_chart_path)
            pdf.image(intent_chart_path, x=40, w=120)
            
        pdf.add_page()
        pdf.ln(15)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(128, 128, 128)
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
