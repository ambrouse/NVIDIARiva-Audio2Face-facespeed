---
name: logging-skill
description: 'Những quy tắt bắt buộc khi ghi và quản lý logs cho dự án (logs của phiên làm việt chứ không phải logs debug cho code)'
argument-hint: 'tuân thủ các quy tắc đã đề ra.'
user-invocable: true
---

# logging-skill
Những quy tắt bắt buộc khi ghi và quản lý logs cho dự án:

## Lưu trữ
- Tất cả logs đều phải lưu trong folder tổng là logs ở project tổng.
- Mỗi task phải ghi lại một logs có chia folder rõ ràng từng loại khác nhau và sắp xếp gọn gàn dễ hiểu.
- Nếu các logs có liên quan đến nhau bạn có thể gom vào chung 1 file và tóm tắt lại.
- Khi bạn sửa hay fix, thêm, thực hiện task nào đó thì phải ghi lại logs của task đó với các thông tin chi tiết như tạo follder gì, fix gì, sửa gì, thêm gì, thực hiện task gì, thời gian thực hiện, thời gian hoàn thành, v.v... để sau này có thể dễ dàng tra cứu lại.
- Luôn quét lại follder logs sau mỗi task để đảm bảo logs được lưu trữ gọn gàng, sạch sẽ, dễ hiểu, dễ tra cứu và không bị rối loạn, nếu có dấu hiệu rối hay không gọn gàng thì phải clean, xóa, sửa logs ngay lập tức để đảm bảo logs luôn được lưu trữ một cách gọn gàng, sạch sẽ, dễ hiểu, dễ tra cứu và không bị rối loạn.

## Tóm tắt
- Mỗi file log không quá dài chỉ tóm tắt lại đúng những điểm quan trọng, trọng tâm.
- Luôn quét lại hết các file doc và tóm tắt, clean, xóa, sửa nếu cần sau mỗi task.


## Format
- Log phải có thời gian rõ ràng.
- Log phải có nội dung rõ ràng, dễ hiểu, dễ tra cứu.
- Log phải có thông tin chi tiết về task đã thực hiện như tạo folder gì, fix gì, sửa gì, thêm gì, thực hiện task gì, thời gian thực hiện, thời gian hoàn thành, v.v...
- Log phải được sắp xếp gọn gàng, sạch sẽ, dễ hiểu, dễ tra cứu và không bị rối loạn.
