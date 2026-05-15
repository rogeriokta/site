import cv2
import numpy as np
from pathlib import Path
from typing import Optional

LABELS = ["A", "B", "C", "D", "E"]


class CardProcessor:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.original = None
        self.warped = None
        self.binary = None
        self._load()

    def _load(self):
        self.original = cv2.imread(self.image_path)
        if self.original is None:
            raise ValueError(f"Não foi possível carregar imagem: {self.image_path}")

    def detect_card(self) -> Optional[np.ndarray]:
        gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        max_area = 0
        document = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:
                continue
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) == 4 and area > max_area:
                max_area = area
                document = approx
        return document

    def correct_perspective(self, contour: np.ndarray, width: int = 2100, height: int = 2970):
        pts = contour.reshape(4, 2).astype(np.float32)
        pts = pts[pts[:, 1].argsort()]
        top = pts[:2][pts[:2][:, 0].argsort()]
        bottom = pts[2:][pts[2:][:, 0].argsort()[::-1]]
        src = np.array([top[0], top[1], bottom[1], bottom[0]], dtype=np.float32)
        dst = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(src, dst)
        self.warped = cv2.warpPerspective(self.original, matrix, (width, height))
        return self.warped

    def _enhance(self) -> np.ndarray:
        gray = cv2.cvtColor(self.warped, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def binarize(self):
        enhanced = self._enhance()
        self.binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return self.binary

    def extract_answers(self) -> dict:
        if self.binary is None:
            self.binarize()

        h, w = self.binary.shape
        sections = {
            "A": {"rect": (0.05, 0.05, 0.45, 0.48)},
            "B": {"rect": (0.52, 0.05, 0.45, 0.48)},
            "C": {"rect": (0.05, 0.52, 0.45, 0.48)},
            "D": {"rect": (0.52, 0.52, 0.45, 0.48)},
        }

        results = {}
        total_q = 0

        for sid, spec in sections.items():
            rx, ry, rw, rh = spec["rect"]
            x1, y1 = int(w * rx), int(h * ry)
            x2, y2 = int(w * (rx + rw)), int(h * (ry + rh))
            roi = self.binary[y1:y2, x1:x2]

            rh_, rw_ = roi.shape
            num_q = 10
            num_alt = 5
            qh = rh_ / num_q
            aw = rw_ / num_alt

            questions = []
            for qi in range(num_q):
                alts = []
                for ai in range(num_alt):
                    cx = int(ai * aw + aw * 0.1)
                    cy = int(qi * qh + qh * 0.1)
                    cw = int(aw * 0.8)
                    ch = int(qh * 0.8)
                    cell = roi[cy:cy + ch, cx:cx + cw]
                    if cell.size == 0:
                        alts.append({"label": LABELS[ai], "filled": 0.0})
                        continue
                    white = cv2.countNonZero(cell)
                    ratio = 1.0 - (white / cell.size)
                    alts.append({"label": LABELS[ai], "filled": round(ratio, 4)})
                alts.sort(key=lambda x: x["filled"], reverse=True)
                best = alts[0]
                questions.append({
                    "number": total_q + qi + 1,
                    "chosen": best["label"] if best["filled"] > 0.25 else None,
                    "confidence": round(best["filled"], 3),
                    "alternatives": alts,
                })
            total_q += num_q
            results[sid] = {"questions": questions}

        return results

    def process(self, gabarito: Optional[dict] = None) -> dict:
        contour = self.detect_card()
        if contour is None:
            raise ValueError("Cartão não detectado na imagem")

        self.correct_perspective(contour)
        self.warped = cv2.GaussianBlur(self.warped, (3, 3), 0)
        answers = self.extract_answers()

        total = 0
        correct = 0
        details = []

        for sid, section in answers.items():
            for q in section["questions"]:
                total += 1
                expected = (gabarito or {}).get(str(q["number"]))
                hit = expected is not None and q["chosen"] == expected
                if hit:
                    correct += 1
                details.append({
                    "number": q["number"],
                    "chosen": q["chosen"],
                    "expected": expected,
                    "confidence": q["confidence"],
                    "correct": hit,
                })

        score = round(correct / total * 100, 1) if total > 0 else 0
        confidence_values = [d["confidence"] for d in details if d["confidence"] is not None]
        avg_confidence = round(sum(confidence_values) / len(confidence_values), 3) if confidence_values else 0

        return {
            "detected": True,
            "width": self.warped.shape[1],
            "height": self.warped.shape[0],
            "answers": answers,
            "details": details,
            "total_questions": total,
            "correct_answers": correct if gabarito else None,
            "score": score if gabarito else None,
            "confidence": avg_confidence,
        }

    def get_processed_bytes(self) -> bytes:
        if self.warped is None:
            raise ValueError("Nenhuma imagem processada")
        _, buf = cv2.imencode(".jpg", self.warped, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return buf.tobytes()
