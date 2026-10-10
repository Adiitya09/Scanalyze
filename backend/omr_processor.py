import cv2
import numpy as np
from PIL import Image
import json
import time
from typing import Dict, List, Tuple, Optional
import os

try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class OMRProcessor:
    def __init__(self):
        self.confidence_threshold = 0.42
        self.min_fill_threshold = 0.20
        self.bubble_min_area = 50
        self.bubble_max_area = 5000
        self.aspect_ratio_threshold = 0.35
        self.target_width = 1000
        
    def process_omr_sheet(self, file_path: str, total_questions: int, number_of_choices: int = 4) -> Dict:
        """
        Main function to process OMR sheet and extract answers.
        
        Args:
            file_path: Path to the OMR sheet image/PDF
            total_questions: Number of questions in the exam
            number_of_choices: Number of choices per question (4 for A-D, 5 for A-E, etc.)
            
        Returns:
            Dictionary containing extracted answers and processing info
        """
        start_time = time.time()
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Validate file format
            if not validate_omr_format(file_path):
                raise ValueError("Unsupported file format. Please use JPG, JPEG, PNG, or PDF")
            
            # Handle PDF files
            if file_path.lower().endswith('.pdf'):
                image = self._convert_pdf_to_image(file_path)
            else:
                image = cv2.imread(file_path)
            
            if image is None:
                raise ValueError("Could not load image file. The file may be corrupted or in an unsupported format.")
            
            # Normalize resolution to target_width for consistent scale across different cameras/scanners
            h, w = image.shape[:2]
            if w > 0 and w != self.target_width:
                scale = self.target_width / float(w)
                new_h = int(h * scale)
                image = cv2.resize(image, (self.target_width, new_h), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
            
            # Process the image
            processed_image = self._preprocess_image(image)
            contours = self._detect_bubbles(processed_image)
            
            if not contours:
                raise ValueError("No bubbles detected in the image. Please check the image quality and format.")
                
            bubbles = self._filter_bubbles(contours, processed_image)
            
            if not bubbles:
                raise ValueError("No valid bubbles found after filtering. Please check the image quality.")
                
            answers = self._extract_answers(bubbles, total_questions, number_of_choices)
            
            processing_time = float(round(time.time() - start_time, 3))
            confidence = float(self._calculate_confidence(bubbles, answers, total_questions, number_of_choices))
            
            return {
                "success": True,
                "answers": answers,
                "confidence": confidence,
                "processing_time": processing_time,
                "total_bubbles_detected": int(len(bubbles)),
                "message": "OMR sheet processed successfully"
            }
            
        except FileNotFoundError as e:
            return {
                "success": False,
                "answers": {},
                "confidence": 0.0,
                "processing_time": float(round(time.time() - start_time, 3)),
                "total_bubbles_detected": 0,
                "message": f"File not found: {str(e)}"
            }
        except ValueError as e:
            return {
                "success": False,
                "answers": {},
                "confidence": 0.0,
                "processing_time": float(round(time.time() - start_time, 3)),
                "total_bubbles_detected": 0,
                "message": f"Invalid input: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "answers": {},
                "confidence": 0.0,
                "processing_time": float(round(time.time() - start_time, 3)),
                "total_bubbles_detected": 0,
                "message": f"Error processing OMR sheet: {str(e)}"
            }
    
    def _convert_pdf_to_image(self, pdf_path: str) -> np.ndarray:
        """Convert PDF to image for processing."""
        if not PDF_SUPPORT:
            raise ValueError("pdf2image library is not installed. Please upload JPG or PNG files.")
        try:
            images = convert_from_path(pdf_path, dpi=300)
            if not images:
                raise ValueError("Could not convert PDF to image - no pages found")
            
            # Use the first page
            pil_image = images[0]
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            err_msg = str(e)
            if "poppler" in err_msg.lower() or "page count" in err_msg.lower():
                raise ValueError("PDF conversion requires Poppler installed in system PATH. Please upload JPG or PNG files.")
            raise ValueError(f"PDF conversion error: {err_msg}")
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess the image for better bubble detection."""
        # Convert to grayscale if color
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold to handle uneven lighting and shadows
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Apply morphological operations to clean up the binary image
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def _detect_bubbles(self, processed_image: np.ndarray) -> List:
        """Detect potential bubble contours in the image."""
        contours, _ = cv2.findContours(
            processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        return contours
    
    def _filter_bubbles(self, contours: List, image: np.ndarray) -> List[Dict]:
        """Filter contours to identify actual bubble marks."""
        bubbles = []
        
        for contour in contours:
            # Calculate contour properties
            area = cv2.contourArea(contour)
            if area < self.bubble_min_area or area > self.bubble_max_area:
                continue
            
            # Check if contour is roughly circular
            perimeter = cv2.arcLength(contour, True)
            if perimeter <= 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.25:  # Not circular enough
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            if h == 0:
                continue
            aspect_ratio = float(w) / h
            if abs(aspect_ratio - 1.0) > self.aspect_ratio_threshold:
                continue
            
            # Calculate fill ratio (how much of the bubble is filled)
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [contour], 255)
            filled_pixels = cv2.countNonZero(cv2.bitwise_and(image, mask))
            total_pixels = area
            fill_ratio = float(filled_pixels / total_pixels) if total_pixels > 0 else 0.0
            
            bubbles.append({
                'contour': contour,
                'center': (x + w//2, y + h//2),
                'area': float(area),
                'fill_ratio': fill_ratio,
                'bounding_box': (x, y, w, h),
                'circularity': float(circularity)
            })
        
        # Sort bubbles by position (top to bottom, left to right)
        bubbles.sort(key=lambda b: (b['center'][1], b['center'][0]))
        
        return bubbles
    
    def _extract_answers(self, bubbles: List[Dict], total_questions: int, number_of_choices: int = 4) -> Dict[str, str]:
        """
        Extract answers from detected bubbles.
        Correctly detects multiple-marked questions and ambiguous marks.
        """
        answers = {}
        
        if not bubbles:
            return answers
        
        # Group bubbles by rows (questions)
        rows = self._group_bubbles_by_rows(bubbles)
        
        # Generate choices based on number_of_choices (A, B, C, D for 4, A, B, C, D, E for 5, etc.)
        choices = [chr(ord('A') + i) for i in range(number_of_choices)]
        
        question_num = 1
        for row in rows[:total_questions]:  # Limit to expected number of questions
            if not row:
                question_num += 1
                continue
            
            # Sort bubbles in row by x-coordinate (left to right)
            row.sort(key=lambda b: b['center'][0])
            
            # Collect all choices that exceed the confidence threshold in this row
            filled_choices = []
            max_fill_ratio = 0.0
            candidate_choice = None
            
            for i, bubble in enumerate(row[:number_of_choices]):  # Limit to configured number of choices
                if i >= len(choices):
                    continue
                choice_letter = choices[i]
                ratio = float(bubble['fill_ratio'])
                
                if ratio > self.confidence_threshold:
                    filled_choices.append((choice_letter, ratio))
                    
                if ratio > max_fill_ratio:
                    max_fill_ratio = ratio
                    candidate_choice = choice_letter
            
            # If multiple bubbles are filled above threshold, mark as MULTIPLE
            if len(filled_choices) > 1:
                answers[str(question_num)] = "MULTIPLE"
            elif len(filled_choices) == 1:
                answers[str(question_num)] = filled_choices[0][0]
            # If no bubbles exceed threshold, the question remains unanswered (omitted from answers dict)
            
            question_num += 1
        
        return answers
    
    def _group_bubbles_by_rows(self, bubbles: List[Dict]) -> List[List[Dict]]:
        """Group bubbles into rows based on y-coordinate."""
        if not bubbles:
            return []
        
        rows = []
        current_row = [bubbles[0]]
        row_threshold = 30  # pixels
        
        for bubble in bubbles[1:]:
            current_row_y = current_row[0]['center'][1]
            bubble_y = bubble['center'][1]
            
            if abs(bubble_y - current_row_y) <= row_threshold:
                current_row.append(bubble)
            else:
                rows.append(current_row)
                current_row = [bubble]
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _calculate_confidence(self, bubbles: List[Dict], answers: Dict[str, str], total_questions: int, number_of_choices: int) -> float:
        """Calculate overall confidence score for the processing."""
        if not bubbles:
            return 0.0
        
        # Base confidence on number of questions answered vs total bubbles
        answered_questions = len(answers)
        total_bubbles = len(bubbles)
        
        if total_bubbles == 0:
            return 0.0
        
        # Calculate average fill ratio of answered bubbles
        fill_ratios = []
        for bubble in bubbles:
            if bubble['fill_ratio'] > self.confidence_threshold:
                fill_ratios.append(float(bubble['fill_ratio']))
        
        avg_fill_ratio = float(np.mean(fill_ratios)) if fill_ratios else 0.0
        
        # Calculate confidence based on multiple factors
        expected_bubbles = total_questions * number_of_choices
        answer_ratio = min(1.0, answered_questions / total_questions) if total_questions > 0 else 0.0
        detection_ratio = min(1.0, total_bubbles / max(expected_bubbles, 1)) if expected_bubbles > 0 else 0.0
        confidence = min(1.0, (avg_fill_ratio * 0.4 + answer_ratio * 0.4 + detection_ratio * 0.2))
        
        return float(round(confidence, 2))
    
    def debug_omr_processing(self, file_path: str, total_questions: int, number_of_choices: int = 4) -> Dict:
        """Debug version with detailed processing information."""
        try:
            if file_path.lower().endswith('.pdf'):
                image = self._convert_pdf_to_image(file_path)
            else:
                image = cv2.imread(file_path)
            
            if image is None:
                return {"error": "Could not load image"}
            
            # Normalize resolution
            h, w = image.shape[:2]
            if w > 0 and w != self.target_width:
                scale = self.target_width / float(w)
                new_h = int(h * scale)
                image = cv2.resize(image, (self.target_width, new_h), interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR)
            
            processed_image = self._preprocess_image(image)
            contours = self._detect_bubbles(processed_image)
            bubbles = self._filter_bubbles(contours, processed_image)
            
            debug_info = {
                "total_contours_found": len(contours),
                "bubbles_after_filtering": len(bubbles),
                "bubble_details": []
            }
            
            for i, bubble in enumerate(bubbles):
                debug_info["bubble_details"].append({
                    "index": i,
                    "center": bubble['center'],
                    "area": round(float(bubble['area']), 2),
                    "fill_ratio": round(float(bubble['fill_ratio']), 3),
                    "circularity": round(float(bubble['circularity']), 3),
                    "bounding_box": bubble['bounding_box']
                })
            
            # Group into rows for analysis
            rows = self._group_bubbles_by_rows(bubbles)
            debug_info["rows_detected"] = len(rows)
            debug_info["row_analysis"] = []
            
            for i, row in enumerate(rows):
                row_info = {
                    "row_index": i,
                    "bubbles_in_row": len(row),
                    "bubbles": []
                }
                
                row.sort(key=lambda b: b['center'][0])  # Sort by x-coordinate
                for j, bubble in enumerate(row):
                    row_info["bubbles"].append({
                        "position": j,
                        "fill_ratio": round(float(bubble['fill_ratio']), 3),
                        "above_min_threshold": bool(bubble['fill_ratio'] > self.min_fill_threshold),
                        "above_confidence_threshold": bool(bubble['fill_ratio'] > self.confidence_threshold)
                    })
                
                debug_info["row_analysis"].append(row_info)
            
            return debug_info
            
        except Exception as e:
            return {"error": str(e)}

# Utility functions for testing
def create_sample_omr_data(total_questions: int) -> Dict[str, str]:
    """Create sample OMR data for testing."""
    choices = ['A', 'B', 'C', 'D']
    answers = {}
    
    for i in range(1, total_questions + 1):
        answers[str(i)] = str(np.random.choice(choices))
    
    return answers

def validate_omr_format(file_path: str) -> bool:
    """Validate if the file is a supported OMR format."""
    if not os.path.exists(file_path):
        return False
    
    if not os.path.isfile(file_path):
        return False
        
    supported_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Check file size (prevent empty or too large files)
    try:
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False
        # Max size: 10MB
        if file_size > 10 * 1024 * 1024:
            return False
    except:
        return False
        
    return file_extension in supported_extensions
