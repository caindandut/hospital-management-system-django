## 📚 Luồng hoạt động hệ thống

### 1. Luồng đăng nhập & phân quyền

**Bước 1 – Đăng nhập**

User vào trang login (URL trong theme/accounts).

Nhập username/password → Django auth xác thực.

Nếu sai: trả lại form + thông báo lỗi.

Nếu đúng: tạo session, lưu request.user, redirect:

Mặc định: LOGIN_REDIRECT_URL = '/admin-portal/' (admin/staff),

Hoặc tùy logic trong view sẽ điều hướng theo role (PATIENT/DOCTOR/STAFF/ADMIN).

**Bước 2 – Xác định vai trò (role)**

Role được suy ra từ:

Nhóm quyền, hoặc

Các profile liên kết (patient profile, doctor profile, staff profile).

context_processors đưa thông tin role (is_patient, is_doctor, …) vào mọi template.

Giao diện sẽ hiển thị menu/ánh xạ đến từng khu vực: /doctors/, /staff/, /admin-portal/, phần bệnh nhân.

### 2. Luồng bệnh nhân đặt lịch khám

URL chính (appointments/urls.py):

appointments/new/ → chọn thông tin ban đầu.

appointments/new/slots/ → chọn slot.

appointments/new/confirm/ → xác nhận.

appointments/my/ → xem lịch hẹn.

appointments/<pk>/cancel/ → hủy lịch.

Chi tiết:

**Chọn thông tin khám – `new_step1`**

Bệnh nhân (đã login) vào /appointments/new/.

View tải danh sách bác sĩ/chuyên khoa, có thể chọn:

Chuyên khoa, hoặc bác sĩ cụ thể.

Ngày dự kiến khám.

Submit form → dữ liệu (specialty/doctor/date) được lưu tạm (session/hidden field) → redirect sang bước 2.

**Chọn slot trống – `new_step2`**

View /appointments/new/slots/ đọc dữ liệu từ bước 1.

Query các lịch làm việc (Schedule) của bác sĩ + các Appointment đã đặt:

Tính các giờ trống (slot).

Render danh sách slot → bệnh nhân chọn 1 slot cụ thể → submit.

**Xác nhận và tạo lịch – `new_step3`**

View /appointments/new/confirm/ nhận slot đã chọn.

Tính/hiển thị:

Thông tin bác sĩ, chuyên khoa.

Ngày giờ khám.

Phí khám (từ doctors.pricing + rank/chuyên khoa).

Khi bệnh nhân bấm xác nhận:

Tạo bản ghi Appointment trong DB.

Gán patient = request.user (qua patient profile).

Set trạng thái: Pending/Confirmed (tùy logic).

Redirect sang my_appointments hoặc trang thông báo thành công.

**Xem lịch hẹn – `my_appointments`**

/appointments/my/ lấy danh sách Appointment lọc theo bệnh nhân hiện tại.

Phân trang + hiển thị trạng thái: Pending, Confirmed, Completed, Cancelled,…

**Hủy lịch hẹn – `cancel_appointment`**

/appointments/<pk>/cancel/ kiểm tra:

Lịch hẹn có thuộc về bệnh nhân hiện tại không?

Còn đủ thời gian để hủy không?

→ So sánh datetime now với appointment_time, dựa trên

APPOINTMENT_CANCEL_BEFORE_MINUTES = 120 trong settings.py.

Nếu hợp lệ → cập nhật status Cancelled.

Nếu quá hạn → hiển thị thông báo lỗi (không cho hủy).

### 3. Luồng bác sĩ: quản lý lịch & khám bệnh

#### 3.1 Quản lý lịch làm việc (Schedule)

URL (appointments/urls.py):

/appointments/doctor/schedule/ → danh sách lịch (schedule_index).

/appointments/doctor/schedule/create/ → tạo lịch (schedule_create).

/appointments/doctor/schedule/<id>/open/ → mở lịch (schedule_open).

/appointments/doctor/schedule/<id>/close/ → đóng lịch (schedule_close).

Chi tiết:

Bác sĩ login → truy cập menu dành cho bác sĩ.

Ở màn hình quản lý lịch:

Xem các lịch làm việc hiện có: ngày, khung giờ, trạng thái (open/closed).

Tạo lịch mới: nhập ngày, khoảng thời gian, số slot, v.v.

Mở/đóng lịch:

open → cho phép bệnh nhân đặt lịch trong khoảng đó.

close → ngừng nhận lịch mới (nhưng vẫn giữ lịch đã đặt).

#### 3.2 Luồng khám bệnh theo từng appointment

URL chính:

/appointments/doctor/today/ → danh sách lịch hôm nay (doctor_today).

/appointments/doctor/pending/ → các lịch chờ (pending_appointments).

/appointments/<pk>/start/ → bắt đầu khám (appt_start).

/appointments/<pk>/record/ → ghi nhận khám (appt_record).

/appointments/<pk>/prescribe/ → kê thuốc (appt_prescribe).

/appointments/<pk>/complete/ → kết thúc (appt_complete).

Chi tiết luồng:

**Xem danh sách lịch hôm nay**

/appointments/doctor/today/ lấy tất cả appointment:

doctor = request.user.doctor_profile

date = hôm nay.

Hiển thị theo giờ, trạng thái.

**Bắt đầu khám – `appt_start`**

Bác sĩ click vào một lịch → /appointments/<pk>/start/.

View:

Kiểm tra appointment có thuộc bác sĩ không.

Cập nhật trạng thái: ví dụ Confirmed → In Progress/Checked-in.

Có thể lưu thời điểm bắt đầu.

Redirect sang trang ghi nhận khám.

**Ghi nhận thông tin khám – `appt_record`**

/appointments/<pk>/record/ hiển thị form:

Triệu chứng, chẩn đoán, cận lâm sàng, kết luận, ghi chú,…

Submit:

Lưu vào model EMR tương ứng (ví dụ Visit/MedicalRecord trong emr/models.py).

Liên kết với appointment và patient.

**Kê thuốc – `appt_prescribe`**

/appointments/<pk>/prescribe/:

Lấy danh sách thuốc (được admin cấu hình trong adminpanel).

Bác sĩ chọn thuốc, liều lượng, số ngày, hướng dẫn.

Lưu prescription liên kết với appointment.

**Kết thúc khám – `appt_complete`**

/appointments/<pk>/complete/:

Kiểm tra đã có record & prescription đủ điều kiện.

Cập nhật appointment: status = Completed.

Có thể trigger tạo hóa đơn, hoặc đánh dấu “sẵn sàng lập hóa đơn” ở khâu billing.

**In tóm tắt & toa thuốc (app `doctors`)**

Các URL:

/doctors/visit-summary/<appointment_id>/ → xem tóm tắt khám.

/doctors/visit-summary/<appointment_id>/print/ → bản in.

/doctors/visit-summary/<appointment_id>/pdf/ → PDF.

/doctors/print-prescription/<appointment_id>/ → in toa thuốc.

Các view này đọc EMR + Prescription rồi render template print-friendly.

### 4. Luồng hóa đơn: Billing & thu ngân (Staff)

#### 4.1 Tạo hóa đơn từ lịch hẹn

URL (billing/urls.py):

/billing/invoice/create-from-appt/<appointment_id>/ → invoice_create_from_appt.

Chi tiết:

Khi appointment ở trạng thái Completed, bác sĩ hoặc hệ thống/nhân viên có thể:

Gọi view invoice_create_from_appt (trực tiếp từ nút “Tạo hóa đơn” trong giao diện).

View:

Lấy appointment, bác sĩ, rank, đơn thuốc, dịch vụ,…

Sử dụng doctors.pricing và bảng RankFee/Specialty trong adminpanel để:

Tính phí khám theo rank.

Tính tiền thuốc (nếu có bảng giá thuốc).

Tạo bản ghi Invoice + InvoiceItem trong billing/models.py.

Đặt trạng thái unpaid.

#### 4.2 Thu ngân xử lý thanh toán

URL (staff/urls.py):

/staff/cashier/ → danh sách hóa đơn chưa thanh toán (cashier_invoices).

/staff/cashier/paid/ → danh sách đã thanh toán (cashier_paid_invoices).

/staff/cashier/invoice/<pk>/ → chi tiết hóa đơn (cashier_invoice_detail).

/staff/cashier/invoice/<pk>/print/ → in hóa đơn (invoice_print).

/staff/cashier/invoice/<pk>/pay/ → thu tiền mặt (invoice_pay_cash).

Chi tiết:

Staff login → vào /staff/cashier/:

View lấy tất cả Invoice chưa thanh toán, có phân trang/lọc theo ngày.

Khi bệnh nhân tới quầy:

Staff chọn 1 hóa đơn → /staff/cashier/invoice/<pk>/:

Hiển thị chi tiết dịch vụ, tổng tiền, VAT (nếu có), trạng thái.

Thu tiền:

Staff bấm “Thanh toán tiền mặt” → /staff/cashier/invoice/<pk>/pay/:

View xác nhận, sau đó:

Set paid = True.

Lưu paid_at = now, paid_by = staff.

In hóa đơn:

/staff/cashier/invoice/<pk>/print/:

Render template in (billing/invoice_print.html) → có thể in giấy hoặc xuất PDF.

### 5. Luồng Admin Portal: quản lý toàn hệ thống

URL (adminpanel/urls.py):

Dashboard:

/admin-portal/ → dashboard.

/admin-portal/debug/ → debug_dashboard.

Lịch hẹn:

/admin-portal/appointments/ → danh sách.

/admin-portal/appointments/<pk>/ → chi tiết.

Bác sĩ:

/admin-portal/doctors/, .../create/, .../<id>/update/, .../<id>/toggle/, .../<id>/delete/.

Bệnh nhân:

/admin-portal/patients/ → patients_list.

/admin-portal/patients/create/, /<pk>/edit/, /<pk>/update/, /<pk>/delete/.

Staff:

Tương tự: list/create/update/delete.

Hóa đơn:

/admin-portal/invoices/, /billing/invoices/, /billing/invoice/<pk>/, /invoices/<pk>/print/, /billing/invoice/<pk>/cash/.

Cấu hình (settings):

settings/specialty/... → chuyên khoa.

settings/rankfee/... → bảng giá theo rank.

settings/drug/... → thuốc.

settings/user/... → user hệ thống.

Luồng chính:

**Dashboard tổng hợp**

Admin login → /admin-portal/.

View lấy các thống kê:

Số lịch hôm nay, đã hoàn thành/chờ khám.

Doanh thu theo khoảng thời gian.

Số bệnh nhân mới, v.v. (tùy code thực tế trong views.py).

**Quản lý dữ liệu nghiệp vụ**

Bác sĩ:

Thêm/sửa/thay đổi trạng thái hoạt động → ảnh hưởng tới việc hiện trong danh sách đặt lịch & pricing.

Bệnh nhân:

Tạo bệnh nhân mới, chỉnh sửa thông tin, xóa (hoặc soft delete).

Staff:

Tạo tài khoản nhân viên thu ngân, gán quyền.

Hóa đơn:

Admin xem được tất cả hóa đơn, có thể:

Xem chi tiết.

In lại.

Đánh dấu thanh toán tiền mặt từ phía admin (khi cần điều chỉnh).

**Cấu hình hệ thống**

Thiết lập chuyên khoa, rank, bảng giá rank fee:

Ảnh hưởng trực tiếp đến cách hệ thống tính phí khám trong billing.

Thiết lập danh mục thuốc:

Bác sĩ dùng trong kê đơn.

Quản lý user:

Gán role, nhóm quyền, reset password, khóa/mở user.

### 6. Luồng kỹ thuật: Request → View → Model → Template

Bất kỳ chức năng nào đều đi theo pattern:

Trình duyệt gọi URL (ví dụ /appointments/new/).

clinic/urls.py chuyển tới appointments.urls.

appointments/urls.py map tới hàm view new_step1.

View:

Kiểm tra login/role.

Đọc request.GET/POST.

Làm việc với models (query, create, update).

Tạo context và gọi render(request, '...html', context) hoặc redirect(...).

Template:

Render HTML với Bootstrap, các custom template tag (vi_format, consult_fee, vnd, v.v.).

Nhận thêm context global từ context_processors (user info, role flags).
