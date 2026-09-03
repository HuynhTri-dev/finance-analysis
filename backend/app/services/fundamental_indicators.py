"""
name: fundamental_indicators.py
description: Fundamental analysis service for Vietnamese listed companies.
             Calculates Piotroski F-Score (0-9) with full mathematical formulas,
             source statement item mapping (KQKD, CĐKT, LCTT), step-by-step
             calculation breakdowns, and full 2-year audit comparison table.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


def _extract_val(df: Optional[pd.DataFrame], item_ids: List[str], year_col: str) -> float:
    """Safely extract a float value from a vnstock statement dataframe."""
    if df is None or df.empty or year_col not in df.columns:
        return 0.0
    for i_id in item_ids:
        row = df[df["item_id"] == i_id]
        if not row.empty:
            val = row[year_col].values[0]
            if pd.notna(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue
    return 0.0


class FundamentalService:
    """
    Computes fundamental quality and valuation metrics for a stock symbol.
    F-Score definition follows Piotroski (2000) — 9 binary signals across
    three pillars: Profitability (4), Leverage & Liquidity (3), and Operating Efficiency (2).
    """

    def calculate_f_score_details(self, symbol: str) -> Dict[str, Any]:
        empty_result = {
            "f_score": None,
            "has_data": False,
            "error_msg": "Doanh nghiệp chưa công bố đủ lịch sử 2 năm BCTC kiểm toán gần nhất.",
            "pillars": {
                "profitability": {"score": 0, "max": 4, "name": "Khả năng sinh lời"},
                "leverage": {"score": 0, "max": 3, "name": "Đòn bẩy & Thanh khoản"},
                "efficiency": {"score": 0, "max": 2, "name": "Hiệu quả hoạt động"},
            },
            "signals": [],
            "statement_table": [],
            "raw_metrics": {},
        }

        try:
            from vnstock import Finance
            logger.info("Fetching financial statements for %s", symbol)

            f_vci = Finance(symbol=symbol, source="VCI")
            inc = f_vci.income_statement(period="year", lang="en")
            bal = f_vci.balance_sheet(period="year", lang="en")
            cf = f_vci.cash_flow(period="year", lang="en")

            if inc is None or bal is None or cf is None or inc.empty or bal.empty or cf.empty:
                logger.warning("No financial statements available for %s", symbol)
                return empty_result

            # Extract available year columns (4-digit strings)
            inc_years = [c for c in inc.columns if str(c).isdigit() and len(str(c)) == 4]
            bal_years = [c for c in bal.columns if str(c).isdigit() and len(str(c)) == 4]
            cf_years = [c for c in cf.columns if str(c).isdigit() and len(str(c)) == 4]

            common_years = sorted(list(set(inc_years) & set(bal_years) & set(cf_years)), reverse=True)

            if len(common_years) < 2:
                logger.warning("Fewer than 2 common fiscal years for %s: %s", symbol, common_years)
                return empty_result

            y_t = common_years[0]   # Latest fiscal year
            y_t1 = common_years[1]  # Prior fiscal year
            logger.info("Using fiscal years %s (t) and %s (t-1) for %s", y_t, y_t1, symbol)

            # --- Extract raw statement values -------------------------------
            # Income statement
            net_income_t = _extract_val(inc, ["net_profit_loss_after_tax", "attributable_to_parent_company"], y_t)
            net_income_t1 = _extract_val(inc, ["net_profit_loss_after_tax", "attributable_to_parent_company"], y_t1)
            revenue_t = _extract_val(inc, ["net_sales", "sales"], y_t)
            revenue_t1 = _extract_val(inc, ["net_sales", "sales"], y_t1)
            gross_profit_t = _extract_val(inc, ["gross_profit"], y_t)
            gross_profit_t1 = _extract_val(inc, ["gross_profit"], y_t1)

            # Balance sheet
            assets_t = _extract_val(bal, ["total_assets"], y_t)
            assets_t1 = _extract_val(bal, ["total_assets"], y_t1)
            cur_assets_t = _extract_val(bal, ["current_assets"], y_t)
            cur_assets_t1 = _extract_val(bal, ["current_assets"], y_t1)
            cur_liab_t = _extract_val(bal, ["current_liabilities"], y_t)
            cur_liab_t1 = _extract_val(bal, ["current_liabilities"], y_t1)
            long_debt_t = _extract_val(bal, ["long_term_liabilities", "long_term_borrowings"], y_t)
            long_debt_t1 = _extract_val(bal, ["long_term_liabilities", "long_term_borrowings"], y_t1)
            shares_t = _extract_val(bal, ["common_shares", "ordinary_shares", "charter_capital"], y_t)
            shares_t1 = _extract_val(bal, ["common_shares", "ordinary_shares", "charter_capital"], y_t1)

            # Cash flow statement
            cfo_t = _extract_val(cf, ["net_cash_inflows_outflows_from_operating_activities"], y_t)
            cfo_t1 = _extract_val(cf, ["net_cash_inflows_outflows_from_operating_activities"], y_t1)

            # If total assets are 0 or missing, data is invalid
            if assets_t <= 0:
                logger.warning("Total assets <= 0 for %s in year %s", symbol, y_t)
                return empty_result

            # --- PILLAR 1: PROFITABILITY (4 Points) ------------------------
            roa_t = net_income_t / max(assets_t, 1.0)
            roa_t1 = net_income_t1 / max(assets_t1, 1.0)

            f1 = int(roa_t > 0)
            f2 = int(cfo_t > 0)
            f3 = int(roa_t > roa_t1)
            f4 = int(cfo_t > net_income_t)
            prof_score = f1 + f2 + f3 + f4

            # --- PILLAR 2: LEVERAGE & LIQUIDITY (3 Points) ------------------
            lev_t = long_debt_t / max(assets_t, 1.0)
            lev_t1 = long_debt_t1 / max(assets_t1, 1.0)
            cur_ratio_t = cur_assets_t / max(cur_liab_t, 1.0) if cur_liab_t > 0 else 1.0
            cur_ratio_t1 = cur_assets_t1 / max(cur_liab_t1, 1.0) if cur_liab_t1 > 0 else 1.0

            f5 = int(lev_t < lev_t1) if (lev_t1 > 0 or lev_t > 0) else 1
            f6 = int(cur_ratio_t > cur_ratio_t1)
            f7 = int(shares_t <= shares_t1 * 1.005) if shares_t1 > 0 else 1
            lev_score = f5 + f6 + f7

            # --- PILLAR 3: OPERATING EFFICIENCY (2 Points) ------------------
            gm_t = gross_profit_t / max(abs(revenue_t), 1.0)
            gm_t1 = gross_profit_t1 / max(abs(revenue_t1), 1.0)
            turn_t = revenue_t / max(assets_t, 1.0)
            turn_t1 = revenue_t1 / max(assets_t1, 1.0)

            f8 = int(gm_t > gm_t1)
            f9 = int(turn_t > turn_t1)
            eff_score = f8 + f9

            total_f_score = prof_score + lev_score + eff_score

            # Format helpers
            def _bil(val: float) -> str:
                return f"{round(val / 1e9, 1):,} tỷ"

            def _pct(val: float) -> str:
                return f"{round(val * 100, 2)}%"

            # Complete audit criteria list
            signals = [
                {
                    "id": "F1",
                    "pillar": "Sinh lời",
                    "title": "ROA dương (Lợi nhuận ròng / Tổng tài sản > 0)",
                    "passed": bool(f1),
                    "value": _pct(roa_t),
                    "formula": "ROA = Lợi nhuận sau thuế (LNST) / Tổng tài sản",
                    "calculation": f"{_bil(net_income_t)} / {_bil(assets_t)} = {_pct(roa_t)}",
                    "source_statement": "KQKD (Mã 60: LNST) ÷ CĐKT (Mã 270: Tổng tài sản)",
                    "condition": f"ROA {_pct(roa_t)} > 0 ➔ {'ĐẠT (+1đ)' if f1 else 'KHÔNG ĐẠT (0đ)'}",
                    "desc": f"Năm {y_t}: Doanh nghiệp có lợi nhuận dương trên tổng tài sản đầu tư.",
                },
                {
                    "id": "F2",
                    "pillar": "Sinh lời",
                    "title": "Dòng tiền CFO dương (Tiền từ HĐKD > 0)",
                    "passed": bool(f2),
                    "value": _bil(cfo_t),
                    "formula": "CFO = Lưu chuyển tiền thuần từ hoạt động kinh doanh",
                    "calculation": f"CFO({y_t}) = {_bil(cfo_t)}",
                    "source_statement": "Báo cáo LCTT (Mã 20: Lưu chuyển tiền thuần từ HĐKD)",
                    "condition": f"CFO {_bil(cfo_t)} > 0 ➔ {'ĐẠT (+1đ)' if f2 else 'KHÔNG ĐẠT (0đ)'}",
                    "desc": f"Năm {y_t}: Hoạt động kinh doanh cốt lõi tạo ra dòng tiền mặt thực tế dương.",
                },
                {
                    "id": "F3",
                    "pillar": "Sinh lời",
                    "title": "ROA tăng trưởng so với năm trước (ΔROA > 0)",
                    "passed": bool(f3),
                    "value": f"{_pct(roa_t)} ({y_t}) vs {_pct(roa_t1)} ({y_t1})",
                    "formula": "ΔROA = ROA(năm nay) - ROA(năm trước)",
                    "calculation": f"ROA({y_t}) {_pct(roa_t)} vs ROA({y_t1}) {_pct(roa_t1)} (Chênh lệch: {round((roa_t - roa_t1) * 100, 2)}%)",
                    "source_statement": "So sánh ROA 2 niên độ BCTC liên tiếp",
                    "condition": f"ROA({y_t}) > ROA({y_t1}) ➔ {'ĐẠT (+1đ)' if f3 else 'KHÔNG ĐẠT (0đ: ROA sụt giảm so với năm trước)'}",
                    "desc": f"Hiệu suất sinh lời tài sản {'cải thiện tăng trưởng so với năm trước.' if f3 else 'suy giảm so với năm trước.'}",
                },
                {
                    "id": "F4",
                    "pillar": "Sinh lời",
                    "title": "Chất lượng lợi nhuận (CFO > LNST)",
                    "passed": bool(f4),
                    "value": f"CFO {_bil(cfo_t)} vs LNST {_bil(net_income_t)}",
                    "formula": "Accruals Check = CFO - LNST > 0",
                    "calculation": f"CFO {_bil(cfo_t)} vs LNST {_bil(net_income_t)} (Chênh lệch tiền mặt: {_bil(cfo_t - net_income_t)})",
                    "source_statement": "LCTT (Mã 20: CFO) đối chiếu KQKD (Mã 60: LNST)",
                    "condition": f"CFO > LNST ➔ {'ĐẠT (+1đ: Dòng tiền thực thu vượt lợi nhuận kế toán)' if f4 else 'KHÔNG ĐẠT (0đ: Lợi nhuận kế toán cao hơn tiền mặt thu về)'}",
                    "desc": "Kiểm tra chất lượng kế toán: Dòng tiền thực tế so với lợi nhuận trên sổ sách.",
                },
                {
                    "id": "F5",
                    "pillar": "Đòn bẩy",
                    "title": "Giảm đòn bẩy nợ dài hạn (ΔLeverage < 0)",
                    "passed": bool(f5),
                    "value": f"{_pct(lev_t)} ({y_t}) vs {_pct(lev_t1)} ({y_t1})",
                    "formula": "Tỷ lệ nợ dài hạn = Nợ dài hạn / Tổng tài sản",
                    "calculation": f"{_bil(long_debt_t)} / {_bil(assets_t)} = {_pct(lev_t)} ({y_t}) so với {_pct(lev_t1)} ({y_t1})",
                    "source_statement": "CĐKT (Mã 330: Nợ dài hạn) ÷ CĐKT (Mã 270: Tổng tài sản)",
                    "condition": f"Nợ dài hạn/Tài sản({y_t}) < Nợ dài hạn/Tài sản({y_t1}) ➔ {'ĐẠT (+1đ: Giảm tỷ trọng nợ vay)' if f5 else 'KHÔNG ĐẠT (0đ: Tỷ lệ nợ dài hạn gia tăng)'}",
                    "desc": f"Doanh nghiệp {'giảm thiểu áp lực nợ vay dài hạn.' if f5 else 'gia tăng tỷ lệ nợ dài hạn trên tổng tài sản.'}",
                },
                {
                    "id": "F6",
                    "pillar": "Đòn bẩy",
                    "title": "Thanh khoản hiện hành cải thiện (Current Ratio tăng)",
                    "passed": bool(f6),
                    "value": f"{round(cur_ratio_t, 2)}x ({y_t}) vs {round(cur_ratio_t1, 2)}x ({y_t1})",
                    "formula": "Current Ratio = Tài sản ngắn hạn / Nợ ngắn hạn",
                    "calculation": f"{_bil(cur_assets_t)} / {_bil(cur_liab_t)} = {round(cur_ratio_t, 2)}x ({y_t}) so với {round(cur_ratio_t1, 2)}x ({y_t1})",
                    "source_statement": "CĐKT (Mã 100: TS ngắn hạn) ÷ CĐKT (Mã 310: Nợ ngắn hạn)",
                    "condition": f"Current Ratio({y_t}) > Current Ratio({y_t1}) ➔ {'ĐẠT (+1đ: Khả năng trả nợ ngắn hạn tăng)' if f6 else 'KHÔNG ĐẠT (0đ: Thanh khoản suy giảm)'}",
                    "desc": f"Khả năng đảm bảo nghĩa vụ nợ ngắn hạn {'cải thiện tốt hơn.' if f6 else 'suy giảm so với năm trước.'}",
                },
                {
                    "id": "F7",
                    "pillar": "Đòn bẩy",
                    "title": "Không pha loãng cổ phiếu (Số CP không tăng)",
                    "passed": bool(f7),
                    "value": f"{round(shares_t / 1e6, 1)}M CP ({y_t}) vs {round(shares_t1 / 1e6, 1)}M CP ({y_t1})" if shares_t > 1e6 else "Không phát hành thêm",
                    "formula": "Dilution Check = Số cổ phiếu lưu hành(năm nay) <= Số cổ phiếu(năm trước) * 1.005",
                    "calculation": f"Năm {y_t}: {shares_t:,.0f} CP vs Năm {y_t1}: {shares_t1:,.0f} CP",
                    "source_statement": "CĐKT (Mã 411: Cổ phiếu phổ thông) hoặc Vốn điều lệ",
                    "condition": f"Cổ phiếu không tăng > 0.5% ➔ {'ĐẠT (+1đ: Không pha loãng EPS)' if f7 else 'KHÔNG ĐẠT (0đ: Có phát hành thêm cổ phiếu mới)'}",
                    "desc": f"{'Không phát hành thêm cổ phiếu làm suy giảm giá trị của cổ đông.' if f7 else 'Có phát hành thêm cổ phiếu làm pha loãng chỉ số EPS.'}",
                },
                {
                    "id": "F8",
                    "pillar": "Hiệu quả",
                    "title": "Biên lợi nhuận gộp tăng trưởng (ΔGross Margin > 0)",
                    "passed": bool(f8),
                    "value": f"{_pct(gm_t)} ({y_t}) vs {_pct(gm_t1)} ({y_t1})",
                    "formula": "Gross Margin = Lợi nhuận gộp / Doanh thu thuần",
                    "calculation": f"{_bil(gross_profit_t)} / {_bil(revenue_t)} = {_pct(gm_t)} ({y_t}) so với {_pct(gm_t1)} ({y_t1})",
                    "source_statement": "KQKD (Mã 20: LN gộp) ÷ KQKD (Mã 10: Doanh thu thuần)",
                    "condition": f"Gross Margin({y_t}) > Gross Margin({y_t1}) ➔ {'ĐẠT (+1đ: Quản trị giá vốn tốt hơn)' if f8 else 'KHÔNG ĐẠT (0đ: Biên lãi gộp co hẹp)'}",
                    "desc": f"Biên lợi nhuận gộp {'tăng trưởng, cải thiện vị thế giá sản phẩm.' if f8 else 'co hẹp do giá vốn tăng hoặc giảm giá bán.'}",
                },
                {
                    "id": "F9",
                    "pillar": "Hiệu quả",
                    "title": "Vòng quay tổng tài sản tăng (ΔAsset Turnover > 0)",
                    "passed": bool(f9),
                    "value": f"{round(turn_t, 2)}x ({y_t}) vs {round(turn_t1, 2)}x ({y_t1})",
                    "formula": "Asset Turnover = Doanh thu thuần / Tổng tài sản",
                    "calculation": f"{_bil(revenue_t)} / {_bil(assets_t)} = {round(turn_t, 2)}x ({y_t}) so với {round(turn_t1, 2)}x ({y_t1})",
                    "source_statement": "KQKD (Mã 10: Doanh thu thuần) ÷ CĐKT (Mã 270: Tổng tài sản)",
                    "condition": f"Asset Turnover({y_t}) > Asset Turnover({y_t1}) ➔ {'ĐẠT (+1đ: Tối ưu hiệu quả tài sản)' if f9 else 'KHÔNG ĐẠT (0đ: Vòng quay tài sản chậm hơn)'}",
                    "desc": f"Hiệu suất sử dụng tài sản để tạo doanh thu {'cải thiện hiệu quả.' if f9 else 'chậm lại so với năm trước.'}",
                },
            ]

            # Full verification / audit reconciliation table
            statement_table = [
                {
                    "item_name": "Lợi nhuận sau thuế (LNST)",
                    "item_code": "Mã 60 (KQKD)",
                    "statement": "Báo cáo Kết quả Kinh doanh",
                    "val_t": round(net_income_t / 1e9, 1),
                    "val_t1": round(net_income_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F1 (ROA dương), F3 (ROA tăng), F4 (CFO > LNST)",
                },
                {
                    "item_name": "Doanh thu thuần",
                    "item_code": "Mã 10 (KQKD)",
                    "statement": "Báo cáo Kết quả Kinh doanh",
                    "val_t": round(revenue_t / 1e9, 1),
                    "val_t1": round(revenue_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F8 (Biên lãi gộp), F9 (Vòng quay tài sản)",
                },
                {
                    "item_name": "Lợi nhuận gộp",
                    "item_code": "Mã 20 (KQKD)",
                    "statement": "Báo cáo Kết quả Kinh doanh",
                    "val_t": round(gross_profit_t / 1e9, 1),
                    "val_t1": round(gross_profit_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F8 (Biên lãi gộp)",
                },
                {
                    "item_name": "Dòng tiền thuần từ HĐKD (CFO)",
                    "item_code": "Mã 20 (LCTT)",
                    "statement": "Báo cáo Lưu chuyển Tiền tệ",
                    "val_t": round(cfo_t / 1e9, 1),
                    "val_t1": round(cfo_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F2 (CFO dương), F4 (CFO > LNST)",
                },
                {
                    "item_name": "Tổng tài sản",
                    "item_code": "Mã 270 (CĐKT)",
                    "statement": "Bảng Cân đối Kế toán",
                    "val_t": round(assets_t / 1e9, 1),
                    "val_t1": round(assets_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F1 (ROA), F3 (ROA), F5 (Nợ/Tài sản), F9 (Vòng quay)",
                },
                {
                    "item_name": "Tài sản ngắn hạn",
                    "item_code": "Mã 100 (CĐKT)",
                    "statement": "Bảng Cân đối Kế toán",
                    "val_t": round(cur_assets_t / 1e9, 1),
                    "val_t1": round(cur_assets_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F6 (Thanh toán hiện hành Current Ratio)",
                },
                {
                    "item_name": "Nợ ngắn hạn",
                    "item_code": "Mã 310 (CĐKT)",
                    "statement": "Bảng Cân đối Kế toán",
                    "val_t": round(cur_liab_t / 1e9, 1),
                    "val_t1": round(cur_liab_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F6 (Thanh toán hiện hành Current Ratio)",
                },
                {
                    "item_name": "Nợ dài hạn",
                    "item_code": "Mã 330 (CĐKT)",
                    "statement": "Bảng Cân đối Kế toán",
                    "val_t": round(long_debt_t / 1e9, 1),
                    "val_t1": round(long_debt_t1 / 1e9, 1),
                    "unit": "Tỷ VNĐ",
                    "used_in": "F5 (Đòn bẩy nợ dài hạn)",
                },
                {
                    "item_name": "Cổ phiếu lưu hành / Vốn CP",
                    "item_code": "Mã 411 (CĐKT)",
                    "statement": "Bảng Cân đối Kế toán",
                    "val_t": round(shares_t / 1e6, 2) if shares_t > 1e6 else shares_t,
                    "val_t1": round(shares_t1 / 1e6, 2) if shares_t1 > 1e6 else shares_t1,
                    "unit": "Triệu CP" if shares_t > 1e6 else "Đơn vị",
                    "used_in": "F7 (Kiểm tra pha loãng)",
                },
            ]

            raw_metrics = {
                "latest_year": y_t,
                "prior_year": y_t1,
                "net_income_bil": round(net_income_t / 1e9, 1),
                "cfo_bil": round(cfo_t / 1e9, 1),
                "revenue_bil": round(revenue_t / 1e9, 1),
                "roa_pct": round(roa_t * 100, 2),
                "current_ratio": round(cur_ratio_t, 2),
                "gross_margin_pct": round(gm_t * 100, 2),
            }

            return {
                "f_score": total_f_score,
                "has_data": True,
                "latest_year": y_t,
                "prior_year": y_t1,
                "pillars": {
                    "profitability": {"score": prof_score, "max": 4, "name": "Khả năng sinh lời"},
                    "leverage": {"score": lev_score, "max": 3, "name": "Đòn bẩy & Thanh khoản"},
                    "efficiency": {"score": eff_score, "max": 2, "name": "Hiệu quả hoạt động"},
                },
                "signals": signals,
                "statement_table": statement_table,
                "raw_metrics": raw_metrics,
            }

        except Exception as e:
            logger.error("Error calculating F-Score details for %s: %s", symbol, e)
            return empty_result

    def calculate_f_score(self, symbol: str) -> Optional[int]:
        details = self.calculate_f_score_details(symbol)
        return details.get("f_score")

    def get_valuation_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch core valuation ratios from vnstock using KBS source (real data).
        Returns: pe, pb, roe, debt_to_equity
        """
        result = {"pe": None, "pb": None, "roe": None, "debt_to_equity": None}
        try:
            from vnstock import Finance
            f_kbs = Finance(symbol=symbol, source="KBS")
            rat = f_kbs.ratio(period="year", lang="en")

            if rat is None or rat.empty:
                logger.warning("No ratio data from KBS for %s", symbol)
                return result

            for _, r in rat.iterrows():
                i_id = str(r.get("item_id", ""))
                val = r.iloc[2]
                if pd.notna(val):
                    try:
                        num = float(val)
                        if i_id == "pe_ratio" and num > 0:
                            result["pe"] = round(num, 2)
                        elif i_id == "pb_ratio" and num > 0:
                            result["pb"] = round(num, 2)
                        elif i_id == "roe":
                            result["roe"] = round(num, 2)
                        elif i_id == "debt_to_equity":
                            result["debt_to_equity"] = round(num / 100.0, 2) if num > 10 else round(num, 2)
                    except (ValueError, TypeError):
                        continue

            return result
        except Exception as e:
            logger.warning("Error fetching valuation metrics for %s: %s", symbol, e)
            return result


fundamental_service = FundamentalService()
