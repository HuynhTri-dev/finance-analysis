# Nghiên cứu và sử dụng chỉ số chứng khoán trong hệ thống phân tích

> **Mục tiêu:** Chuẩn hoá cách dùng các chỉ số kỹ thuật, cơ bản và rủi ro để nghiên cứu, sàng lọc và kiểm định giả thuyết trên cổ phiếu. Tài liệu không tạo khuyến nghị đầu tư cá nhân, không dự báo chắc chắn giá và không thay thế quản trị rủi ro danh mục.

## 1. Kết luận ngắn

Không có chỉ số đơn lẻ nào quyết định được “nên mua” hoặc “nên bán”. Mỗi nhóm chỉ số trả lời một câu hỏi khác nhau:

| Nhóm | Câu hỏi cần trả lời | Ví dụ |
|---|---|---|
| Xu hướng và biến động | Giá đang đi theo regime nào, biến động có tăng không? | MA, Bollinger Bands, ATR |
| Giá trị và chất lượng | Doanh nghiệp có lợi nhuận, dòng tiền và cấu trúc vốn đáng để nghiên cứu thêm không? | EPS, P/E, ROA, CFO, Piotroski F-Score |
| Rủi ro và bối cảnh | Rủi ro thị trường, thanh khoản và tập trung đang ở mức nào? | beta, độ rộng thị trường, turnover, drawdown |
| Sự kiện | Thông tin mới có khác kỳ vọng hay không? | tăng trưởng lợi nhuận, thay đổi hướng dẫn, lịch công bố |

Các chỉ số chỉ trở nên hữu ích khi được đo bằng dữ liệu đúng thời điểm, đặt trong bối cảnh ngành/regime và kiểm định ngoài mẫu sau chi phí.

## 2. Phạm vi, giả định và chuẩn dữ liệu

### 2.1. Phạm vi phiên bản đầu tiên

- Universe: cổ phiếu có dữ liệu giá, khối lượng và báo cáo tài chính đủ lịch sử.
- Tần suất: EOD cho giá/khối lượng; theo ngày công bố đối với báo cáo tài chính.
- Mục đích: xếp hạng mã cần nghiên cứu, cảnh báo rủi ro và tạo feature cho backtest; không phát lệnh tự động.
- Thị trường và khung thời gian phải được cấu hình rõ. Không chuyển kết quả từ thị trường hoặc giai đoạn khác thành kết luận áp dụng cho Việt Nam.

### 2.2. Dữ liệu tối thiểu

| Dữ liệu | Quy tắc sử dụng |
|---|---|
| OHLCV | Dùng giá đã điều chỉnh cho chia tách/quyền nếu nguồn dữ liệu hỗ trợ; tối thiểu 252 phiên để tính percentile và regime. |
| Báo cáo tài chính | Lưu `published_at`/thời điểm công bố thực tế. Chỉ cho mô hình dùng dữ liệu sau thời điểm này. |
| Benchmark và ngành | Cùng lịch giao dịch với mã; không dùng benchmark thiếu phiên hoặc thay đổi thành phần mà không ghi nhận. |
| Thanh khoản | Cấu hình ngưỡng giá trị giao dịch/turnover; kết quả của mã kém thanh khoản phải có cờ `LOW_LIQUIDITY`. |
| Sự kiện doanh nghiệp | Gắn cờ chia tách, phát hành thêm, cổ tức tiền mặt, trái phiếu chuyển đổi, tạm ngừng giao dịch và tin công bố nếu nguồn dữ liệu có hỗ trợ. Giá, khối lượng, EPS và số cổ phiếu lưu hành phải dùng cùng chính sách điều chỉnh. |

**Điều kiện dừng:** dữ liệu thiếu, nến chưa chốt, dữ liệu tài chính chưa có ngày công bố, hoặc không đạt thanh khoản tối thiểu phải trả về `INSUFFICIENT_DATA`/`LOW_LIQUIDITY`, không suy diễn tín hiệu.

## 3. Danh mục chỉ số

### 3.1. Xu hướng: Moving Average (MA)

Với giá đóng cửa \(P_t\), SMA \(n\) phiên:

$$
SMA_n(t) = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}
$$

EMA đặt trọng số lớn hơn cho giá gần đây; hệ thống phải công bố rõ \(n\), công thức khởi tạo và loại giá dùng để các kết quả có thể tái lập.

| Cách dùng đúng | Không được suy luận |
|---|---|
| Lọc regime: giá trên/dưới MA dài hạn; nhận biết thay đổi xu hướng qua giao cắt MA ngắn/dài. | Giá vượt MA là bằng chứng đủ để mở/đóng vị thế. |
| Đặt bối cảnh cho tín hiệu khác, ví dụ breakout kèm thanh khoản. | Hiệu quả lịch sử của một quy tắc MA ở thị trường khác sẽ lặp lại. |

Quy tắc MA từng cho kết quả có ý nghĩa trong một mẫu Dow Jones lịch sử, nhưng đó là bằng chứng theo mẫu dữ liệu và thiết kế nghiên cứu cụ thể, không phải bảo đảm lợi nhuận. Mọi biến thể phải được kiểm định theo dữ liệu, chi phí và cơ chế khớp lệnh của thị trường mục tiêu.

### 3.2. Biến động: Bollinger Bands

Với đường trung tâm \(MA_n(t)\), độ lệch chuẩn giá \(\sigma_n(t)\) và hệ số \(k\):

$$
Upper_t = MA_n(t) + k\sigma_n(t)
\\qquad
Lower_t = MA_n(t) - k\sigma_n(t)
$$

Thiết lập phổ biến là \(n=20\), \(k=2\), nhưng đây là điểm khởi đầu để kiểm định chứ không phải chuẩn tối ưu. Hệ thống cần tính thêm:

$$
\\%B_t = \frac{P_t - Lower_t}{Upper_t - Lower_t}
\\qquad
Bandwidth_t = \frac{Upper_t - Lower_t}{MA_n(t)}
$$

| Quan sát | Diễn giải thận trọng |
|---|---|
| `Bandwidth` thấp | Biến động đang nén; có thể theo sau bằng mở rộng biến động nhưng không xác định trước hướng. |
| Giá đóng ngoài dải | Giá đang ở vùng biến động tương đối cao/thấp; không tự động là đảo chiều. |
| Giá ngoài dải + volume cao + cấu trúc giá | Là giả thuyết đáng kiểm tra hơn tín hiệu dải đơn lẻ. |

Không dùng diễn giải “±2 độ lệch chuẩn chứa 95% giá” để kết luận xác suất đảo chiều của giá chứng khoán. Chuỗi giá/lợi suất có thể không tuân theo phân phối chuẩn và phụ thuộc vào cách tính độ lệch chuẩn.

### 3.3. Giá trị và lợi nhuận: EPS, P/E, ROA, CFO

| Chỉ số | Công thức/định nghĩa | Cách đọc | Giới hạn |
|---|---|---|---|
| EPS | Lợi nhuận thuộc cổ đông phổ thông / số cổ phiếu bình quân gia quyền | Theo dõi mức và xu hướng lợi nhuận trên mỗi cổ phần. | Bị ảnh hưởng bởi khoản bất thường, mua lại/phát hành cổ phiếu và chính sách kế toán. |
| P/E | Giá thị trường / EPS | So sánh định giá trong cùng ngành, cùng loại EPS và cùng giai đoạn. | Không có ý nghĩa khi EPS âm; P/E cao không tự động là đắt, P/E thấp không tự động là rẻ. |
| ROA | Lợi nhuận ròng / tổng tài sản bình quân | Đo hiệu quả sinh lợi trên tài sản, phù hợp để so sánh xu hướng trong doanh nghiệp/ngành. | Khác biệt mô hình kinh doanh và đòn bẩy có thể làm so sánh chéo ngành sai lệch. |
| CFO | Dòng tiền thuần từ hoạt động kinh doanh | Đối chiếu chất lượng lợi nhuận và khả năng chuyển lợi nhuận thành tiền. | Cần đọc cùng chu kỳ vốn lưu động, đầu tư và chính sách kế toán. |

Hệ thống không được lấy P/E từ các nguồn khác kỳ báo cáo hoặc trộn EPS trailing với EPS forecast mà không gắn nhãn. Với doanh nghiệp tài chính, ngân hàng, bảo hiểm hoặc ngành có cấu trúc vốn đặc biệt, cần có bộ chỉ số riêng thay vì áp dụng máy móc cùng một bộ lọc.

#### 3.3.1. Định giá đa chiều

Không xếp hạng P/E, P/B hay EV/EBITDA trên một thang chung giữa các ngành. Mỗi chỉ số chỉ được chuẩn hoá thành percentile trong **cùng ngành, cùng thời điểm, cùng định nghĩa dữ liệu**.

| Chỉ số | Công thức/định nghĩa | Dùng khi | Giới hạn bắt buộc |
|---|---|---|---|
| P/B | Giá thị trường / (vốn chủ sở hữu / số cổ phiếu lưu hành) | Ngân hàng, bảo hiểm và doanh nghiệp có tài sản hữu hình đáng kể. | Giá trị sổ sách có thể không phản ánh tài sản vô hình hoặc giá thị trường của tài sản. |
| EV/EBITDA | (Vốn hoá + nợ vay − tiền và tương đương tiền) / EBITDA | So sánh doanh nghiệp phi tài chính có đòn bẩy khác nhau. | EBITDA không phải dòng tiền; phải đánh giá capex duy trì, thuê tài sản và nợ ngoài bảng cân đối. |
| PEG | P/E / tăng trưởng EPS kỳ vọng | Kiểm tra P/E cao có đi kèm tăng trưởng dự phóng hợp lý. | Không dùng với EPS/tăng trưởng âm hoặc bất thường; phải lưu nguồn và ngày của dự phóng. |
| Dividend yield / payout | Cổ tức tiền mặt năm / giá; cổ tức / lợi nhuận ròng | Nghiên cứu thu nhập và tính bền vững của phân phối tiền mặt. | Yield cao có thể do giá giảm hoặc lợi nhuận giảm; đọc cùng dòng tiền và lịch sử chi trả. |
| DCF | Giá trị hiện tại của FCF dự phóng và giá trị cuối kỳ. | Neo giá trị nội tại để so sánh với định giá tương đối. | Rất nhạy với WACC, tăng trưởng dài hạn và giả định FCF; bắt buộc có bảng sensitivity. |

$$
V_0 = \sum_{t=1}^{n}\frac{FCF_t}{(1+r)^t} + \frac{TV_n}{(1+r)^n}
$$

Với EPS âm, trả `NOT_APPLICABLE` cho P/E và PEG; tuyệt đối không đưa giá trị âm/vô cực vào điểm xếp hạng. DCF cần công bố rõ năm dự phóng, WACC, tốc độ tăng trưởng cuối kỳ và các kịch bản tăng/giảm trước khi được dùng làm feature.

#### 3.3.2. Phân rã DuPont, thanh khoản và đòn bẩy

DuPont giải thích **nguồn gốc** của ROE thay vì chỉ quan sát mức ROE:

$$
ROE =
\frac{\text{Lợi nhuận ròng}}{\text{Doanh thu}}
\times
\frac{\text{Doanh thu}}{\text{Tổng tài sản bình quân}}
\times
\frac{\text{Tổng tài sản bình quân}}{\text{Vốn chủ sở hữu bình quân}}
$$

| Chỉ số | Cách đọc | Cảnh báo |
|---|---|---|
| Biên lợi nhuận ròng và vòng quay tài sản | ROE tăng nhờ hai yếu tố này thường là bằng chứng vận hành cần nghiên cứu thêm. | Xác nhận CFO, chất lượng lợi nhuận và tính chu kỳ của ngành. |
| Đòn bẩy tài chính | ROE tăng chủ yếu do tổng tài sản/vốn chủ sở hữu tăng cần được tách riêng. | Kiểm tra nợ vay, chi phí lãi, lịch đáo hạn và interest coverage. |
| Current/quick ratio | Khả năng chi trả ngắn hạn; quick ratio loại hàng tồn kho. | Không áp dụng máy móc cho ngân hàng/bảo hiểm. |
| Debt/Equity và interest coverage | Cấu trúc nợ vay và khả năng trả lãi từ EBIT. | So sánh trong ngành; ngưỡng phải cấu hình, không dùng ngưỡng chung. |
| Cash conversion cycle | Ngày tồn kho + ngày phải thu − ngày phải trả. | CCC kéo dài cần được đối chiếu doanh thu, tồn kho, công nợ và CFO. |

Các tỷ số này chỉ là `reason_codes` và feature để kiểm định; chúng không thay thế F-Score hay kết luận nguyên nhân tài chính.

### 3.4. Chất lượng tài chính: Piotroski F-Score

F-Score là tổng của 9 tín hiệu nhị phân, mỗi tín hiệu 0 hoặc 1:

| Trụ cột | Tín hiệu |
|---|---|
| Khả năng sinh lời | ROA dương; CFO dương; ROA tăng; CFO lớn hơn lợi nhuận ròng. |
| Đòn bẩy và vốn | Đòn bẩy dài hạn giảm; current ratio tăng; không phát hành thêm cổ phiếu phổ thông. |
| Hiệu quả hoạt động | Biên lợi nhuận gộp tăng; vòng quay tài sản tăng. |

$$
F\\text{-}Score = \sum_{j=1}^{9} signal_j \\quad \\text{với } signal_j \\in \\{0,1\\}
$$

F-Score là bộ lọc chất lượng cho ứng viên giá trị, không phải thước đo “an toàn tuyệt đối” hay mô hình dự báo lợi suất độc lập. Trước khi áp dụng, phải chuẩn hoá cách tính cho chuẩn báo cáo, niên độ và đặc thù ngành; lưu từng tín hiệu thành phần để người dùng kiểm tra.

### 3.4.1. Khung riêng cho ngân hàng

Ngân hàng có cấu trúc bảng cân đối, nguồn vốn và dòng tiền khác doanh nghiệp phi tài chính. Không dùng chung ngưỡng P/E, ROA, CFO, current ratio hoặc F-Score với nhóm này.

| Chỉ số | Định nghĩa | Cách dùng | Giới hạn |
|---|---|---|---|
| NIM | Thu nhập lãi thuần / tài sản sinh lãi bình quân | Theo dõi hiệu quả hoạt động tín dụng cốt lõi. | So sánh theo cơ cấu tài sản và regime lãi suất. |
| NPL ratio | Dư nợ nhóm 3–5 / tổng dư nợ | Theo dõi chất lượng tài sản. | Đọc cùng thuyết minh, cơ cấu nợ và chính sách phân loại. |
| CAR | Vốn tự có / tài sản có rủi ro quy đổi | Theo dõi sức chịu đựng vốn theo quy định. | Là chỉ số tuân thủ, không dự báo trực tiếp lợi nhuận. |
| CASA ratio | Tiền gửi không kỳ hạn / tổng tiền gửi | Bối cảnh chi phí vốn và lợi thế NIM. | Có thể biến động theo mùa vụ và niềm tin tiền gửi. |
| Dự phòng và LLR | Chi phí dự phòng; tỷ lệ bao phủ nợ xấu | Đọc áp lực chất lượng tài sản lên lợi nhuận. | Chính sách trích lập và chất lượng tài sản khác nhau giữa ngân hàng. |

Universe phải được phân nhóm ít nhất thành `NON_FINANCIAL`, `BANK`, `INSURANCE` và `SECURITIES` trước khi sàng lọc. CAR và cách tính tài sản có rủi ro phải đối chiếu quy định Ngân hàng Nhà nước đang hiệu lực tại thời điểm chạy.

### 3.5. Rủi ro, thanh khoản và bối cảnh thị trường

| Chỉ số | Cách dùng |
|---|---|
| Beta | \(\beta_i = Cov(r_i,r_m) / Var(r_m)\). Là ước lượng phụ thuộc vào benchmark, cửa sổ và tần suất; không thay thế đo lường rủi ro toàn diện. |
| Drawdown | Theo dõi mức giảm từ đỉnh lịch sử/đỉnh cửa sổ; dùng cho giới hạn rủi ro và đánh giá chiến lược. |
| Thanh khoản | Dùng giá trị giao dịch, turnover và tỷ lệ ngày không giao dịch để điều chỉnh tính khả thi của kết quả backtest. |
| Độ rộng thị trường | Ví dụ tỷ lệ mã trên MA50; chỉ là mô tả regime, cần ghi rõ universe và quy tắc loại trừ. |
| Động lượng tương đối | Lợi suất mã trừ lợi suất benchmark trong cùng cửa sổ; dùng để đặt sức mạnh của mã vào bối cảnh thị trường. |

### 3.6. Bối cảnh vĩ mô và sự kiện doanh nghiệp

| Nhóm | Chỉ báo/dữ liệu | Cách dùng an toàn |
|---|---|---|
| Lãi suất | Lãi suất điều hành, liên ngân hàng, lợi suất trái phiếu phù hợp kỳ hạn | Bối cảnh hoá chi phí vốn và định giá; không cộng thẳng vào điểm cổ phiếu. |
| Tỷ giá và dự trữ ngoại hối | Biến động VND/USD, dữ liệu công bố chính thức | Kiểm tra rủi ro chính sách tiền tệ và doanh nghiệp có phơi nhiễm ngoại tệ. |
| Dòng vốn ngoại | Mua/bán ròng theo nguồn, kỳ và phạm vi rõ ràng | Là bối cảnh riêng; không suy diễn từ volume tổng. |
| Chu kỳ ngành | Ví dụ tăng trưởng tín dụng, tồn kho, giá đầu vào | Chọn bộ chỉ số/benchmark đúng ngành, không dùng một proxy cho mọi ngành. |
| Phát hành, ESOP, chuyển đổi | Số cổ phiếu pha loãng, diluted EPS, ngày hiệu lực | Điều chỉnh EPS/BVPS và kiểm tra pha loãng tiềm năng. |
| Chia tách/cổ tức | Giá và khối lượng điều chỉnh; ngày giao dịch không hưởng quyền | Tránh diễn giải gap cơ học là tín hiệu kỹ thuật hoặc thay đổi giá trị doanh nghiệp. |

Nếu nguồn chỉ điều chỉnh một phần sự kiện doanh nghiệp, trả `PARTIAL_ADJUSTMENT` và loại khỏi kết luận so sánh lịch sử nhạy với giá/EPS.

## 4. Cách kết hợp các chỉ số

Kết hợp theo **trình tự quyết định**, không cộng cơ học mọi chỉ số vào một “điểm mua”:

~~~mermaid
flowchart LR
    A[Kiểm tra dữ liệu, sự kiện và thanh khoản] --> B[Bối cảnh vĩ mô và regime thị trường]
    B --> C[Sàng lọc chất lượng/định giá theo ngành]
    C --> D[Đánh giá xu hướng, biến động và rủi ro]
    D --> E[Đưa vào danh sách nghiên cứu]
    E --> F[Backtest / đánh giá con người / quản trị danh mục]
~~~

| Bước | Đầu ra được phép | Không được làm |
|---|---|---|
| Regime | `RISK_ON`, `RISK_OFF`, `NEUTRAL` theo quy tắc đã phiên bản hoá. | Suy diễn mọi mã sẽ biến động cùng chỉ số. |
| Chất lượng/giá trị | Danh sách ứng viên theo ngành, nhóm tài chính/phi tài chính và dữ liệu point-in-time. | Xếp hạng P/E xuyên ngành, dùng chỉ số phi tài chính cho ngân hàng hoặc dùng dữ liệu công bố sau ngày quyết định. |
| Kỹ thuật/rủi ro | `WATCH`, `CAUTION` hoặc cờ rủi ro theo tài liệu high-risk. | Gọi một giao cắt MA hoặc chạm Bollinger Band là lệnh. |
| Danh mục | Đề xuất nghiên cứu tiếp và kiểm tra giới hạn tỷ trọng, ngành, thanh khoản. | Bỏ qua giới hạn rủi ro chỉ vì điểm tổng hợp cao. |

Ví dụ có thể kiểm định: “Trong `RISK_ON`, các mã có F-Score cao theo ngành và momentum tương đối dương có kết quả sau chi phí tốt hơn benchmark cùng universe.” Đây là giả thuyết nghiên cứu; kết quả phải được báo cáo bằng dữ liệu ngoài mẫu.

## 5. Giao thức kiểm định bắt buộc

### 5.1. Đặt giả thuyết trước

Mỗi thử nghiệm phải lưu: universe, giai đoạn, tần suất tái cân bằng, feature, nhãn mục tiêu, rule vào/ra, benchmark, chi phí, thanh khoản giả định và tiêu chí thành công. Không thay đổi ngưỡng sau khi xem kết quả mà vẫn gọi đó là out-of-sample.

### 5.2. Tránh các sai lệch phổ biến

- **Look-ahead bias:** báo cáo tài chính chỉ xuất hiện từ ngày công bố, không phải ngày kết thúc quý/năm.
- **Survivorship bias:** giữ cả mã đã huỷ niêm yết, sáp nhập hoặc ngừng giao dịch khi dữ liệu cho phép.
- **Data snooping:** giới hạn số cấu hình thử nghiệm, giữ riêng tập kiểm thử cuối cùng và ghi số lần thử.
- **Khả năng khớp lệnh:** trừ phí, thuế, bid–ask spread/trượt giá và giới hạn tỷ trọng theo thanh khoản.
- **Overfitting theo regime:** dùng walk-forward validation; báo cáo riêng giai đoạn tăng, giảm và biến động cao.

### 5.3. Thước đo đánh giá

| Mục tiêu | Thước đo tối thiểu |
|---|---|
| Sàng lọc/xếp hạng | hit rate theo quantile, excess return so với benchmark cùng universe, turnover và độ ổn định theo giai đoạn. |
| Quản trị rủi ro | max drawdown, volatility, downside deviation, tỷ lệ phiên không thể khớp giả định. |
| Mô hình xác suất | calibration, Brier score/log loss và hiệu quả sau ngưỡng quyết định. |
| Chiến lược | lợi suất sau chi phí, Sharpe/Sortino, turnover, capacity và kết quả walk-forward. |

Không coi accuracy của chiều giá là đủ. Một mô hình có accuracy cao vẫn có thể không khả thi sau chi phí, sai lệch lớp, thanh khoản và quy mô vị thế.

## 6. Học máy và AI: phạm vi an toàn

ML/AI có thể dùng để xếp hạng, ước lượng xác suất hoặc trích xuất dữ liệu có cấu trúc từ tài liệu. Không được mô tả như công cụ “dự đoán chắc chắn” giá cổ phiếu.

1. Xây baseline đơn giản trước: benchmark, rule MA/Bollinger và mô hình tuyến tính.
2. Feature phải point-in-time; version hoá dữ liệu, mã nguồn, tham số và kết quả.
3. Tách train/validation/test theo thời gian; ưu tiên walk-forward, không xáo trộn chuỗi thời gian.
4. So sánh với baseline sau chi phí và cùng quy tắc tái cân bằng.
5. Theo dõi drift, calibration và hiệu năng sau triển khai; mô hình suy giảm phải bị hạ cấp thành `RESEARCH_ONLY`.
6. LLM chỉ hỗ trợ trích xuất/tóm tắt có dẫn nguồn; số liệu tài chính và quyết định cuối phải được kiểm tra bằng dữ liệu có cấu trúc.

## 7. Quy ước đầu ra và audit trail

Mỗi kết quả phân tích cần chứa:

~~~json
{
  "symbol": "…",
  "as_of": "YYYY-MM-DDTHH:mm:ssZ",
  "data_status": "OK | INSUFFICIENT_DATA | LOW_LIQUIDITY",
  "market_regime": "RISK_ON | RISK_OFF | NEUTRAL",
  "indicators": {"ma": {}, "bollinger": {}, "fundamentals": {}, "risk": {}},
  "flags": ["WATCH"],
  "config_version": "…",
  "source_versions": ["…"]
}
~~~

Không xuất “MUA”, “BÁN”, “chắc chắn tăng” hoặc “chắc chắn giảm” từ mô-đun chỉ số. Hành động, nếu có, phải được quyết định bởi lớp quản trị danh mục độc lập, có giới hạn tỷ trọng và audit trail.

## 8. Tài liệu tham khảo chọn lọc

- [Fama (1970), *Efficient Capital Markets*](https://doi.org/10.1111/j.1540-6261.1970.tb00518.x) — khuôn khổ về hiệu quả thị trường.
- [Brock, Lakonishok & LeBaron (1992), *Simple Technical Trading Rules*](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x) — kiểm định MA và trading-range break trên DJIA lịch sử; không suy rộng tự động sang thị trường khác.
- [John Bollinger, *A Complete Explanation of Bollinger Bands*](https://www.bollingerbands.com/bollinger-bands) — mô tả cấu trúc MA và độ lệch chuẩn của dải.
- [Piotroski (2000), *Value Investing*](https://ideas.repec.org/a/bla/joares/v38y2000ip1-41.html) — nguồn gốc F-Score.
- Aswath Damodaran, *Investment Valuation* — định giá tương đối, DCF và sensitivity analysis.
- Stephen Penman, *Financial Statement Analysis and Security Valuation* — DuPont và chất lượng lợi nhuận.
- [Basel Committee — Standards](https://www.bis.org/bcbs/publications.htm) — nguồn tham chiếu khung an toàn vốn; triển khai tại Việt Nam phải đối chiếu quy định NHNN đang hiệu lực.
- [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_Library.html) — dữ liệu và mô tả nhân tố Fama–French; không dùng trực tiếp làm nhân tố cho Việt Nam nếu chưa tái xây dựng phương pháp.
- [U.S. SEC, *Day Trading: Your Dollars at Risk*](https://www.sec.gov/about/reports-publications/investorpubsdaytipshtm) — nhắc nhở về rủi ro cao của giao dịch ngắn hạn.
