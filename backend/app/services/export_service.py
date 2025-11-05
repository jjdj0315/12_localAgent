"""ExportService for exporting metrics data to CSV and PDF

This service handles data export with automatic downsampling for large datasets
(Feature 002, FR-024, FR-025).
"""
import io
import logging
import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import BinaryIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.models.metric_snapshot import MetricSnapshot
from app.models.metric_type import MetricType

logger = logging.getLogger(__name__)

# Register Korean font for PDF generation
def _register_korean_font():
    """Register NanumGothic font for Korean text in PDFs"""
    try:
        # Try common NanumGothic font paths
        font_paths = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            '/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf',
            '/System/Library/Fonts/AppleGothic.ttf',  # macOS fallback
            'C:\\Windows\\Fonts\\malgun.ttf',  # Windows fallback
        ]

        font_registered = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
                    font_registered = True
                    logger.info(f"한글 폰트 등록 성공: {font_path}")
                    break
                except Exception as e:
                    logger.warning(f"폰트 등록 실패 ({font_path}): {e}")
                    continue

        if not font_registered:
            logger.warning("NanumGothic 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
            return False

        return True
    except Exception as e:
        logger.error(f"폰트 등록 중 오류: {e}")
        return False

# Register font on module load
_KOREAN_FONT_AVAILABLE = _register_korean_font()

# Export configuration
MAX_EXPORT_SIZE_MB = 10
MAX_EXPORT_SIZE_BYTES = MAX_EXPORT_SIZE_MB * 1024 * 1024
EXPORT_EXPIRATION_HOURS = 1


class ExportService:
    """Service for exporting metrics data to various formats"""

    def __init__(self, export_dir: Path):
        """Initialize export service

        Args:
            export_dir: Directory to store temporary export files
        """
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_to_csv(
        self,
        snapshots: list[MetricSnapshot],
        metric_type: str,
        granularity: str,
        include_metadata: bool = True,
        add_bom: bool = True
    ) -> tuple[bytes, bool]:
        """Export metric snapshots to CSV format (FR-024, FR-114)

        Args:
            snapshots: List of metric snapshots to export
            metric_type: Type of metric being exported
            granularity: Data granularity ('hourly' or 'daily')
            include_metadata: Include metadata header rows
            add_bom: Add UTF-8 BOM for Windows compatibility (default True)

        Returns:
            tuple: (CSV data as bytes, whether data was downsampled)
        """
        # Convert to DataFrame
        data = []
        for s in snapshots:
            data.append({
                '시간': s.collected_at.isoformat(),
                '메트릭 타입': s.metric_type,
                '값': s.value,
                '세분성': s.granularity,
                '재시도 횟수': s.retry_count
            })

        df = pd.DataFrame(data)

        # Check estimated size (FR-114: encoding depends on add_bom)
        csv_buffer = io.StringIO()
        encoding = 'utf-8-sig' if add_bom else 'utf-8'
        df.to_csv(csv_buffer, index=False, encoding=encoding)
        estimated_size = len(csv_buffer.getvalue().encode(encoding))

        downsampled = False

        # Downsample if too large (FR-014, FR-015)
        if estimated_size > MAX_EXPORT_SIZE_BYTES:
            logger.warning(f"CSV 크기 초과 ({estimated_size} bytes), 다운샘플링 적용")

            # Calculate target rows to stay under limit
            target_rows = int(len(df) * (MAX_EXPORT_SIZE_BYTES / estimated_size) * 0.9)

            # Simple downsampling: take every nth row
            step = max(1, len(df) // target_rows)
            df = df.iloc[::step].copy()

            downsampled = True
            logger.info(f"다운샘플링 완료: {len(data)} -> {len(df)} 행")

        # Add metadata header if requested
        if include_metadata:
            metadata_lines = [
                f"# 메트릭 내보내기 - {MetricType(metric_type).display_name_ko}",
                f"# 생성 시간: {datetime.now(timezone.utc).isoformat()}",
                f"# 세분성: {granularity}",
                f"# 데이터 포인트: {len(df)}",
                f"# 다운샘플링: {'예' if downsampled else '아니오'}",
                "#"
            ]
            metadata = '\n'.join(metadata_lines) + '\n'
        else:
            metadata = ''

        # Generate final CSV (FR-114: conditional BOM)
        csv_buffer = io.StringIO()
        csv_buffer.write(metadata)
        df.to_csv(csv_buffer, index=False, encoding=encoding)

        csv_data = csv_buffer.getvalue().encode(encoding)

        logger.info(
            f"CSV 생성 완료: {len(csv_data)} bytes, "
            f"{len(df)} 행, 다운샘플링={downsampled}, BOM={add_bom}"
        )

        return csv_data, downsampled

    def export_to_pdf(
        self,
        snapshots: list[MetricSnapshot],
        metric_type: str,
        granularity: str,
        include_chart: bool = False
    ) -> tuple[bytes, bool]:
        """Export metric snapshots to PDF format (FR-025)

        Args:
            snapshots: List of metric snapshots to export
            metric_type: Type of metric being exported
            granularity: Data granularity ('hourly' or 'daily')
            include_chart: Whether to include a chart (not implemented in MVP)

        Returns:
            tuple: (PDF data as bytes, whether data was downsampled)
        """
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=18
        )

        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()

        # Create Korean-compatible styles
        if _KOREAN_FONT_AVAILABLE:
            title_style = ParagraphStyle(
                'KoreanTitle',
                parent=styles['Title'],
                fontName='NanumGothic',
                fontSize=18,
                alignment=TA_CENTER
            )
            normal_style = ParagraphStyle(
                'KoreanNormal',
                parent=styles['Normal'],
                fontName='NanumGothic',
                fontSize=10,
                alignment=TA_LEFT
            )
        else:
            title_style = styles['Title']
            normal_style = styles['Normal']

        # Title
        metric_display = MetricType(metric_type).display_name_ko
        title = Paragraph(
            f"<b>메트릭 리포트: {metric_display}</b>",
            title_style
        )
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Metadata
        now = datetime.now(timezone.utc)
        metadata_text = f"""
        <b>생성 시간:</b> {now.strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>
        <b>세분성:</b> {granularity}<br/>
        <b>데이터 포인트:</b> {len(snapshots)}<br/>
        """
        metadata = Paragraph(metadata_text, normal_style)
        elements.append(metadata)
        elements.append(Spacer(1, 20))

        # Downsample if needed
        downsampled = False
        display_snapshots = snapshots

        # Estimate table size (rough approximation)
        estimated_rows = len(snapshots)
        estimated_size_per_row = 100  # bytes per row (rough estimate)
        estimated_size = estimated_rows * estimated_size_per_row

        if estimated_size > MAX_EXPORT_SIZE_BYTES:
            target_rows = int(estimated_rows * (MAX_EXPORT_SIZE_BYTES / estimated_size) * 0.9)
            step = max(1, len(snapshots) // target_rows)
            display_snapshots = snapshots[::step]
            downsampled = True
            logger.info(f"PDF 다운샘플링: {len(snapshots)} -> {len(display_snapshots)} 행")

        # Data table
        table_data = [['시간', '값', '재시도 횟수']]

        for s in display_snapshots[:500]:  # Limit to 500 rows for PDF readability
            table_data.append([
                s.collected_at.strftime('%Y-%m-%d %H:%M'),
                str(s.value),
                str(s.retry_count)
            ])

        # Create table with Korean font support
        table = Table(table_data, colWidths=[3*inch, 2*inch, 1.5*inch])

        # Table style with Korean font
        table_font = 'NanumGothic' if _KOREAN_FONT_AVAILABLE else 'Helvetica'
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), table_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), table_font),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))

        elements.append(table)

        # Add downsampling notice if applicable
        if downsampled:
            elements.append(Spacer(1, 12))
            notice = Paragraph(
                "<i>참고: 파일 크기 제한으로 데이터가 다운샘플링되었습니다.</i>",
                normal_style
            )
            elements.append(notice)

        # Build PDF
        doc.build(elements)

        pdf_data = buffer.getvalue()
        buffer.close()

        logger.info(f"PDF 생성 완료: {len(pdf_data)} bytes, 다운샘플링={downsampled}")

        return pdf_data, downsampled

    def save_export_file(
        self,
        data: bytes,
        filename: str,
        export_id: str
    ) -> Path:
        """Save export data to temporary file (FR-024)

        Args:
            data: File data as bytes
            filename: Desired filename
            export_id: Unique export identifier

        Returns:
            Path: Path to saved file
        """
        file_path = self.export_dir / f"{export_id}_{filename}"

        with open(file_path, 'wb') as f:
            f.write(data)

        logger.info(f"내보내기 파일 저장: {file_path} ({len(data)} bytes)")

        return file_path

    def cleanup_expired_exports(self):
        """Delete export files older than expiration time (FR-024)

        Removes files older than EXPORT_EXPIRATION_HOURS (1 hour by default)
        """
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=EXPORT_EXPIRATION_HOURS)

        deleted_count = 0

        for file_path in self.export_dir.glob('*'):
            if not file_path.is_file():
                continue

            # Get file modification time
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)

            if mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"만료된 파일 삭제: {file_path}")

        if deleted_count > 0:
            logger.info(f"내보내기 파일 정리 완료: {deleted_count}개 삭제")
