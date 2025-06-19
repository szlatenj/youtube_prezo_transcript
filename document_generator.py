"""
Document generator module for YouTube Presentation Extractor
Creates HTML, Markdown, and PDF documents with screenshots and transcripts
"""

import os
import cv2
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import jinja2
import re

from config import Config
from scene_detector import SceneChange
from transcript_parser import TranscriptParser


@dataclass
class PresentationSlide:
    """Represents a slide with screenshot and transcript."""
    timestamp: float
    screenshot_path: str
    transcript_text: str
    slide_number: int
    enhanced_text: str = ""  # Enhanced version of transcript
    key_points: List[str] = None  # Key points for this slide
    summary: str = ""  # Summary of this slide
    
    def __post_init__(self):
        """Initialize default values for enhanced fields."""
        if self.key_points is None:
            self.key_points = []


class DocumentGenerator:
    """Generates presentation documents from screenshots and transcripts."""
    
    def __init__(self, config: Config):
        self.config = config
        self.slides = []
        self.video_title = ""
        self.video_duration = 0.0
        self.output_path = None  # Store the output path for screenshot directory
        self.enhancement_stats = {}  # Store enhancement statistics
        
        # Setup Jinja2 environment for HTML templates
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates'),
            autoescape=True
        )
    
    def create_presentation(self, 
                          scene_changes: List[SceneChange],
                          transcript_parser: TranscriptParser,
                          video_title: str,
                          video_duration: float,
                          output_filename: str) -> str:
        """
        Create a complete presentation document.
        
        Args:
            scene_changes: List of detected scene changes
            transcript_parser: Parsed transcript data
            video_title: Title of the video
            video_duration: Duration of the video in seconds
            output_filename: Name of output file
            
        Returns:
            Path to the generated document
        """
        self.video_title = video_title
        self.video_duration = video_duration
        
        # Store output path for screenshot directory creation
        self.output_path = os.path.join(self.config.output_directory, output_filename)
        
        print("Generating presentation document...")
        
        # Create slides from scene changes
        self.slides = self._create_slides(scene_changes, transcript_parser)
        
        # Generate document based on format
        format_upper = self.config.output_format.upper()
        if format_upper == "HTML":
            return self._generate_html_document(output_filename)
        elif format_upper == "MARKDOWN":
            return self._generate_markdown_document(output_filename)
        elif format_upper == "PDF":
            return self._generate_pdf_document(output_filename)
        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")
    
    def _create_slides(self, scene_changes: List[SceneChange], 
                      transcript_parser: TranscriptParser) -> List[PresentationSlide]:
        """Create slides from scene changes and transcript data with controlled text length."""
        slides = []
        
        print(f"Creating slides from {len(scene_changes)} scene changes...")
        
        # Define time limit per slide (in seconds) to control text length
        time_limit_per_slide = 300.0  # 5 minutes per slide (increased from 2 minutes)
        
        for i, change in enumerate(scene_changes):
            # Determine the time range for this scene change
            if i == 0:
                start_time = 0.0
                if len(scene_changes) > 1:
                    end_time = scene_changes[1].timestamp
                else:
                    end_time = change.timestamp + time_limit_per_slide
            else:
                start_time = scene_changes[i-1].timestamp
                if i < len(scene_changes) - 1:
                    end_time = scene_changes[i+1].timestamp
                else:
                    end_time = change.timestamp + time_limit_per_slide
            
            # Split this time range into multiple slides if it's too long
            current_time = start_time
            slide_number = len(slides) + 1
            
            while current_time < end_time:
                slide_end_time = min(current_time + time_limit_per_slide, end_time)
                
                # Get all segments within this slide's time range
                segments_in_range = transcript_parser.get_segments_in_range(current_time, slide_end_time)
                
                if segments_in_range:  # Only create slide if there are segments
                    # Combine transcript text from all segments in this range
                    transcript_texts = []
                    enhanced_texts = []
                    all_key_points = []
                    
                    for segment in segments_in_range:
                        # Add original text
                        if segment.text:
                            transcript_texts.append(segment.text)
                        
                        # Add enhanced text if available
                        if segment.enhanced_text and segment.enhanced_text != segment.text:
                            enhanced_texts.append(segment.enhanced_text)
                        else:
                            enhanced_texts.append(segment.text)
                        
                        # Add key points
                        all_key_points.extend(segment.key_points)
                    
                    # Combine all texts
                    transcript_text = " ".join(transcript_texts)
                    enhanced_text = " ".join(enhanced_texts)
                    
                    # Clean the texts and remove markdown formatting
                    if transcript_text:
                        transcript_text = transcript_parser.clean_text(transcript_text)
                    if enhanced_text:
                        enhanced_text = transcript_parser.clean_text(enhanced_text)
                        # Remove markdown formatting from enhanced text
                        enhanced_text = self._remove_markdown_formatting(enhanced_text)
                    
                    # Create slide
                    slide = PresentationSlide(
                        timestamp=current_time,
                        screenshot_path=os.path.join('pics', f"screenshot_{i+1:03d}.{self.config.screenshot_format.lower()}"),
                        transcript_text=transcript_text,
                        slide_number=slide_number,
                        enhanced_text=enhanced_text,
                        key_points=all_key_points
                    )
                    
                    slides.append(slide)
                    slide_number += 1
                
                current_time = slide_end_time
        
        print(f"Created {len(slides)} slides with controlled text length")
        return slides
    
    def _generate_html_document(self, output_filename: str) -> str:
        """Generate HTML presentation document."""
        # Ensure templates directory exists
        os.makedirs('templates', exist_ok=True)
        
        # Create HTML template if it doesn't exist
        self._create_html_template()
        
        # Prepare template data
        template_data = {
            'title': self.video_title,
            'slides': self.slides,
            'total_slides': len(self.slides),
            'video_duration': self.video_duration,
            'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'include_timestamps': self.config.include_timestamps,
            'include_navigation': self.config.include_navigation
        }
        
        # Render template
        template = self.jinja_env.get_template('presentation.html')
        html_content = template.render(**template_data)
        
        # Write to file
        output_path = os.path.join(self.config.output_directory, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated HTML presentation: {output_path}")
        return output_path
    
    def _generate_markdown_document(self, output_filename: str) -> str:
        """Generate Markdown presentation document."""
        output_path = os.path.join(self.config.output_directory, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# {self.video_title}\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"**Video Duration:** {self._format_duration(self.video_duration)}\n")
            f.write(f"**Total Slides:** {len(self.slides)}\n\n")
            
            # Add enhancement info if available
            enhanced_slides = [s for s in self.slides if s.enhanced_text and s.enhanced_text != s.transcript_text]
            if enhanced_slides:
                f.write(f"**Enhanced Content:** {len(enhanced_slides)} slides have AI-enhanced transcripts\n\n")
            
            # Write table of contents
            if self.config.include_navigation:
                f.write("## Table of Contents\n\n")
                for slide in self.slides:
                    timestamp_str = self._format_timestamp(slide.timestamp)
                    f.write(f"- [Slide {slide.slide_number} ({timestamp_str})](#slide-{slide.slide_number})\n")
                f.write("\n---\n\n")
            
            # Write slides
            for slide in self.slides:
                f.write(f"## Slide {slide.slide_number}\n\n")
                
                if self.config.include_timestamps:
                    timestamp_str = self._format_timestamp(slide.timestamp)
                    f.write(f"**Timestamp:** {timestamp_str}\n\n")
                
                # Reference the screenshot image
                f.write(f"![Slide {slide.slide_number}]({slide.screenshot_path})\n\n")
                
                # Add enhanced transcript if available
                if slide.enhanced_text and slide.enhanced_text != slide.transcript_text:
                    f.write("**Enhanced Transcript:**\n\n")
                    f.write(f"{slide.enhanced_text}\n\n")
                    
                    # Add key points if available
                    if slide.key_points:
                        f.write("**Key Points:**\n\n")
                        for point in slide.key_points:
                            f.write(f"- {point}\n")
                        f.write("\n")
                    
                    # Add original transcript as reference
                    if slide.transcript_text:
                        f.write("<details>\n<summary>Original Transcript</summary>\n\n")
                        f.write(f"{slide.transcript_text}\n\n")
                        f.write("</details>\n\n")
                else:
                    # Add original transcript
                    if slide.transcript_text:
                        f.write("**Transcript:**\n\n")
                        f.write(f"{slide.transcript_text}\n\n")
                    else:
                        f.write("*No transcript available for this slide.*\n\n")
                
                f.write("---\n\n")
        
        print(f"Generated Markdown presentation: {output_path}")
        return output_path
    
    def _generate_pdf_document(self, output_filename: str) -> str:
        """Generate PDF presentation document."""
        output_path = os.path.join(self.config.output_directory, output_filename)
        
        # Try WeasyPrint first (better HTML to PDF conversion)
        if self._try_weasyprint_pdf(output_path):
            return output_path
        
        # Fallback to ReportLab
        if self._try_reportlab_pdf(output_path):
            return output_path
        
        # If both fail, generate HTML and suggest manual conversion
        print("Warning: PDF generation failed. Generating HTML instead.")
        html_filename = output_filename.replace('.pdf', '.html')
        return self._generate_html_document(html_filename)
    
    def _try_weasyprint_pdf(self, output_path: str) -> bool:
        """Try to generate PDF using WeasyPrint."""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            print("Generating PDF with WeasyPrint...")
            
            # Generate HTML content first
            html_content = self._generate_pdf_html_content()
            
            # Create PDF
            font_config = FontConfiguration()
            html_doc = HTML(string=html_content, base_url=self.config.output_directory)
            
            # Add CSS for PDF styling
            css_content = self._get_pdf_css()
            css_doc = CSS(string=css_content, font_config=font_config)
            
            html_doc.write_pdf(output_path, stylesheets=[css_doc], font_config=font_config)
            
            print(f"Generated PDF with WeasyPrint: {output_path}")
            return True
            
        except ImportError:
            print("WeasyPrint not available, trying ReportLab...")
            return False
        except Exception as e:
            print(f"WeasyPrint PDF generation failed: {e}")
            return False
    
    def _try_reportlab_pdf(self, output_path: str) -> bool:
        """Generate PDF with ReportLab - completely rewritten."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            print("Generating PDF with ReportLab...")
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # COVER PAGE
            cover_title_style = ParagraphStyle(
                'CoverTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=40,
                alignment=1,  # Center
                textColor=colors.darkblue
            )
            
            cover_meta_style = ParagraphStyle(
                'CoverMeta',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=20,
                alignment=1  # Center
            )
            
            story.append(Paragraph(self.video_title, cover_title_style))
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", cover_meta_style))
            story.append(Paragraph(f"Video Duration: {self._format_duration(self.video_duration)}", cover_meta_style))
            story.append(Paragraph(f"Total Slides: {len(self.slides)}", cover_meta_style))
            story.append(PageBreak())
            
            # SLIDE PAGES
            for slide in self.slides:
                # Slide header
                slide_header_style = ParagraphStyle(
                    'SlideHeader',
                    parent=styles['Heading2'],
                    fontSize=16,
                    spaceAfter=15,
                    textColor=colors.darkblue
                )
                
                slide_header = f"Slide {slide.slide_number}"
                if self.config.include_timestamps:
                    timestamp_str = self._format_timestamp(slide.timestamp)
                    slide_header += f" ({timestamp_str})"
                
                story.append(Paragraph(slide_header, slide_header_style))
                
                # Screenshot image
                screenshot_path = os.path.join(self.config.output_directory, slide.screenshot_path)
                if os.path.exists(screenshot_path):
                    try:
                        img = Image(screenshot_path, width=7*inch, height=4.5*inch)
                        story.append(img)
                        story.append(Spacer(1, 20))
                    except Exception as e:
                        print(f"ERROR: Could not add image {screenshot_path}: {e}")
                        story.append(Paragraph("<i>Image could not be loaded</i>", styles['Italic']))
                        story.append(Spacer(1, 20))
                else:
                    story.append(Paragraph("<i>Screenshot not found</i>", styles['Italic']))
                    story.append(Spacer(1, 20))
                
                # Enhanced transcript (much shorter)
                if slide.enhanced_text and slide.enhanced_text != slide.transcript_text:
                    transcript_style = ParagraphStyle(
                        'Transcript',
                        parent=styles['Normal'],
                        fontSize=11,
                        spaceAfter=20,
                        leading=14,
                        leftIndent=10,
                        rightIndent=10
                    )
                    
                    # Truncate to much shorter length
                    short_text = self._truncate_text_for_slide(slide.enhanced_text, max_words=60)
                    formatted_text = self._format_text_for_pdf(short_text)
                    story.append(Paragraph(formatted_text, transcript_style))
                elif slide.transcript_text:
                    # Fallback to original transcript
                    transcript_style = ParagraphStyle(
                        'Transcript',
                        parent=styles['Normal'],
                        fontSize=11,
                        spaceAfter=20,
                        leading=14,
                        leftIndent=10,
                        rightIndent=10
                    )
                    short_text = self._truncate_text_for_slide(slide.transcript_text, max_words=60)
                    story.append(Paragraph(short_text, transcript_style))
                else:
                    story.append(Paragraph("<i>No transcript available for this slide.</i>", styles['Italic']))
                
                # Page break for next slide
                story.append(PageBreak())
            
            # Build PDF
            doc.build(story)
            
            print(f"Generated PDF with ReportLab: {output_path}")
            return True
            
        except ImportError:
            print("ReportLab not available.")
            return False
        except Exception as e:
            print(f"ReportLab PDF generation failed: {e}")
            return False
    
    def _generate_pdf_html_content(self) -> str:
        """Generate HTML content optimized for PDF conversion."""
        # Create HTML template if it doesn't exist
        self._create_html_template()
        
        # Prepare template data
        template_data = {
            'title': self.video_title,
            'slides': self.slides,
            'total_slides': len(self.slides),
            'video_duration': self.video_duration,
            'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'include_timestamps': self.config.include_timestamps,
            'include_navigation': False  # Disable navigation for PDF
        }
        
        # Render template
        template = self.jinja_env.get_template('presentation.html')
        return template.render(**template_data)
    
    def _get_pdf_css(self) -> str:
        """Get CSS optimized for PDF generation."""
        return """
        @page {
            margin: 1in;
            size: A4;
        }
        
        body {
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.4;
            margin: 0;
            padding: 0;
        }
        
        .container {
            max-width: none;
            margin: 0;
            padding: 0;
        }
        
        h1 {
            font-size: 18pt;
            text-align: center;
            margin-bottom: 20pt;
            page-break-after: avoid;
        }
        
        .metadata {
            font-size: 10pt;
            margin-bottom: 20pt;
            page-break-after: avoid;
        }
        
        .slide {
            page-break-before: always;
            margin-bottom: 20pt;
        }
        
        .slide:first-child {
            page-break-before: avoid;
        }
        
        .slide-header {
            font-size: 14pt;
            font-weight: bold;
            margin-bottom: 10pt;
            page-break-after: avoid;
        }
        
        .slide-content {
            margin: 0;
        }
        
        .screenshot {
            max-width: 100%;
            height: auto;
            margin-bottom: 10pt;
            page-break-inside: avoid;
            border: 1px solid #ddd;
            border-radius: 3pt;
        }
        
        .transcript {
            font-size: 10pt;
            margin-top: 10pt;
            page-break-inside: avoid;
        }
        
        .timestamp {
            font-size: 9pt;
            color: #666;
            margin-bottom: 5pt;
        }
        
        .navigation {
            display: none;
        }
        """
    
    def _create_html_template(self):
        """Create the default HTML template."""
        template_path = os.path.join('templates', 'presentation.html')
        
        if os.path.exists(template_path):
            return
        
        template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Presentation</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        .metadata {
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .slide {
            margin-bottom: 40px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        .slide-header {
            background-color: #34495e;
            color: white;
            padding: 15px;
            margin: 0;
        }
        .slide-content {
            padding: 20px;
        }
        .screenshot {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .transcript {
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #3498db;
            border-radius: 0 5px 5px 0;
        }
        .timestamp {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .navigation {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navigation h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .navigation a {
            display: block;
            padding: 5px 0;
            color: #3498db;
            text-decoration: none;
        }
        .navigation a:hover {
            color: #2980b9;
        }
        .no-transcript {
            color: #7f8c8d;
            font-style: italic;
        }
        @media (max-width: 768px) {
            .navigation {
                position: static;
                margin-bottom: 20px;
            }
        }
        @media print {
            .navigation {
                display: none;
            }
            body {
                background-color: white;
            }
            .container {
                box-shadow: none;
                border-radius: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        
        <div class="metadata">
            <p><strong>Generated:</strong> {{ generated_date }}</p>
            <p><strong>Video Duration:</strong> {{ "%.2f"|format(video_duration) }} seconds</p>
            <p><strong>Total Slides:</strong> {{ total_slides }}</p>
        </div>

        {% if include_navigation %}
        <div class="navigation">
            <h3>Navigation</h3>
            {% for slide in slides %}
            <a href="#slide-{{ slide.slide_number }}">Slide {{ slide.slide_number }}</a>
            {% endfor %}
        </div>
        {% endif %}

        {% for slide in slides %}
        <div class="slide" id="slide-{{ slide.slide_number }}">
            <h2 class="slide-header">Slide {{ slide.slide_number }}</h2>
            <div class="slide-content">
                {% if include_timestamps %}
                <div class="timestamp">
                    <strong>Timestamp:</strong> {{ "%.2f"|format(slide.timestamp) }}s
                </div>
                {% endif %}
                
                <div class="screenshot-placeholder">
                    <p><em>Screenshot not saved to disk</em></p>
                </div>
                
                <div class="transcript">
                    <h4>Transcript:</h4>
                    {% if slide.transcript_text %}
                    <p>{{ slide.transcript_text }}</p>
                    {% else %}
                    <p class="no-transcript">No transcript available for this slide.</p>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>"""
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp in HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def save_screenshots(self, frames: List[tuple], scene_changes: List[SceneChange]) -> List[str]:
        """
        Save screenshot images for detected scene changes to a pics folder.
        
        Args:
            frames: List of (timestamp, frame) tuples
            scene_changes: List of detected scene changes
            
        Returns:
            List of screenshot file paths
        """
        import cv2
        import os
        
        screenshot_paths = []
        
        # Create pics directory under output directory
        pics_dir = os.path.join(self.config.output_directory, 'pics')
        os.makedirs(pics_dir, exist_ok=True)
        
        print(f"Saving screenshots to: {pics_dir}")
        
        for i, change in enumerate(scene_changes):
            # Find the closest frame to the scene change timestamp
            closest_frame = None
            min_diff = float('inf')
            
            for timestamp, frame in frames:
                diff = abs(timestamp - change.timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest_frame = frame
            
            if closest_frame is not None:
                # Generate filename and save the image
                filename = f"screenshot_{i+1:03d}.{self.config.screenshot_format.lower()}"
                filepath = os.path.join(pics_dir, filename)
                
                # Save the image
                cv2.imwrite(filepath, closest_frame)
                
                # Store relative path for HTML/PDF generation
                relative_path = os.path.join('pics', filename)
                screenshot_paths.append(relative_path)
            else:
                # Fallback if no frame found
                filename = f"screenshot_{i+1:03d}.{self.config.screenshot_format.lower()}"
                relative_path = os.path.join('pics', filename)
                screenshot_paths.append(relative_path)
        
        print(f"Saved {len(screenshot_paths)} screenshots")
        return screenshot_paths
    
    def _remove_markdown_formatting(self, text: str) -> str:
        """Remove markdown formatting from text."""
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Remove markdown lists
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove markdown code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def _format_text_for_pdf(self, text: str) -> str:
        """Format text for PDF generation by removing markdown and adding line breaks."""
        # Remove markdown formatting
        text = self._remove_markdown_formatting(text)
        
        # Add line breaks
        text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text)
        
        return text.strip()

    def _truncate_text_for_slide(self, text: str, max_words: int = 150) -> str:
        """
        Truncate text to fit on a slide with image.
        
        Args:
            text: Text to truncate
            max_words: Maximum words allowed per slide
            
        Returns:
            Truncated text that fits on the slide
        """
        if not text:
            return text
        
        # Split into sentences to avoid cutting mid-sentence
        sentences = text.split('. ')
        
        truncated_text = ""
        word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # Check if adding this sentence would exceed the limit
            if word_count + sentence_words > max_words:
                # If we have some content, add ellipsis
                if truncated_text:
                    truncated_text += "..."
                break
            
            # Add the sentence
            if truncated_text:
                truncated_text += ". " + sentence
            else:
                truncated_text = sentence
            
            word_count += sentence_words
        
        return truncated_text.strip()
    
    def _enhance_slides_with_llm(self, slides: List[PresentationSlide], 
                                transcript_parser: TranscriptParser,
                                transcript_enhancer: 'TranscriptEnhancer',
                                enhancement_level: str) -> List[PresentationSlide]:
        """
        Enhance transcripts for batches of 2-3 slides at once.
        
        Args:
            slides: List of slides with time ranges
            transcript_parser: Transcript parser with segments
            transcript_enhancer: LLM enhancer
            enhancement_level: Enhancement level
            
        Returns:
            List of slides with enhanced transcripts
        """
        enhanced_slides = []
        batch_size = 3  # Process 3 slides at once
        
        for i in range(0, len(slides), batch_size):
            batch_slides = slides[i:i + batch_size]
            print(f"Processing batch of {len(batch_slides)} slides (slides {i+1}-{i+len(batch_slides)})")
            
            # Get time range for this batch
            batch_start = batch_slides[0].timestamp
            batch_end = batch_slides[-1].timestamp + 120.0  # Add 2 minutes for last slide
            
            # Get all segments within this batch's time range
            segments_in_range = transcript_parser.get_segments_in_range(batch_start, batch_end)
            
            if segments_in_range:
                # Combine original text for enhancement
                original_texts = []
                for segment in segments_in_range:
                    if segment.text:
                        original_texts.append(segment.text)
                
                combined_original_text = " ".join(original_texts)
                combined_original_text = transcript_parser.clean_text(combined_original_text)
                
                # Enhance the combined text for multiple slides
                try:
                    enhanced_result = transcript_enhancer.enhance_transcript_segment(
                        type('Segment', (), {'text': combined_original_text})(),
                        enhancement_level
                    )
                    
                    # Split enhanced text across the slides in this batch
                    enhanced_text = self._remove_markdown_formatting(enhanced_result.enhanced_text)
                    split_texts = self._split_text_for_slides(enhanced_text, len(batch_slides))
                    
                    # Create enhanced slides
                    for j, slide in enumerate(batch_slides):
                        enhanced_slide = PresentationSlide(
                            timestamp=slide.timestamp,
                            screenshot_path=slide.screenshot_path,
                            transcript_text=slide.transcript_text,  # Keep original
                            slide_number=slide.slide_number,
                            enhanced_text=split_texts[j] if j < len(split_texts) else "",
                            key_points=enhanced_result.key_points if j == 0 else []  # Key points only on first slide
                        )
                        
                        enhanced_slides.append(enhanced_slide)
                    
                except Exception as e:
                    print(f"Warning: Failed to enhance batch {i//batch_size + 1}: {e}")
                    enhanced_slides.extend(batch_slides)
            else:
                enhanced_slides.extend(batch_slides)
        
        return enhanced_slides
    
    def _split_text_for_slides(self, text: str, num_slides: int) -> List[str]:
        """
        Split enhanced text across multiple slides.
        
        Args:
            text: Enhanced text to split
            num_slides: Number of slides to split across
            
        Returns:
            List of text portions for each slide
        """
        if num_slides <= 1:
            return [text]
        
        # Split into sentences
        sentences = text.split('. ')
        
        # Calculate sentences per slide
        sentences_per_slide = max(1, len(sentences) // num_slides)
        
        slide_texts = []
        for i in range(num_slides):
            start_idx = i * sentences_per_slide
            end_idx = start_idx + sentences_per_slide if i < num_slides - 1 else len(sentences)
            
            slide_sentences = sentences[start_idx:end_idx]
            slide_text = '. '.join(slide_sentences)
            
            # Ensure it ends with a period
            if slide_text and not slide_text.endswith('.'):
                slide_text += '.'
            
            slide_texts.append(slide_text)
        
        return slide_texts
    
    def create_presentation_with_slides(self, slides: List[PresentationSlide],
                                      video_title: str,
                                      video_duration: float,
                                      output_filename: str) -> str:
        """
        Create a presentation document from pre-defined slides.
        
        Args:
            slides: List of slides with content
            video_title: Title of the video
            video_duration: Duration of the video in seconds
            output_filename: Name of output file
            
        Returns:
            Path to the generated document
        """
        self.video_title = video_title
        self.video_duration = video_duration
        self.slides = slides
        
        # Store output path for screenshot directory creation
        self.output_path = os.path.join(self.config.output_directory, output_filename)
        
        print("Generating presentation document...")
        
        # Generate document based on format
        format_upper = self.config.output_format.upper()
        if format_upper == "HTML":
            return self._generate_html_document(output_filename)
        elif format_upper == "MARKDOWN":
            return self._generate_markdown_document(output_filename)
        elif format_upper == "PDF":
            return self._generate_pdf_document(output_filename)
        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")
    
    def _save_enhanced_transcript_by_slides(self, slides: List[PresentationSlide], output_path: str) -> bool:
        """
        Save enhanced transcript organized by slides.
        
        Args:
            slides: List of slides with enhanced content
            output_path: Path to save the enhanced transcript
            
        Returns:
            True if saved successfully
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("Enhanced Transcript by Slides\n")
                f.write("=" * 50 + "\n\n")
                
                for slide in slides:
                    f.write(f"Slide {slide.slide_number} (Timestamp: {self._format_timestamp(slide.timestamp)})\n")
                    f.write("-" * 40 + "\n")
                    
                    if slide.enhanced_text and slide.enhanced_text != slide.transcript_text:
                        f.write("Enhanced Transcript:\n")
                        f.write(f"{slide.enhanced_text}\n\n")
                        
                        if slide.key_points:
                            f.write("Key Points:\n")
                            for point in slide.key_points:
                                f.write(f"  - {point}\n")
                            f.write("\n")
                        
                        f.write("Original Transcript:\n")
                        f.write(f"{slide.transcript_text}\n")
                    else:
                        f.write(f"{slide.transcript_text}\n")
                    
                    f.write("\n" + "=" * 50 + "\n\n")
            
            print(f"Enhanced transcript saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving enhanced transcript: {e}")
            return False 