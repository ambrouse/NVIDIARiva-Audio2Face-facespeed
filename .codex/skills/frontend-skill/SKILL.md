---
name: frontend-skill
description: 'Những quy tắt bắt buộc khi viết code frontend.'
argument-hint: 'tuân thủ các quy tắc đã đề ra.'
user-invocable: true
---
# Frontend Skill

Những quy tắt bắt buộc khi viết code frontend.

## Nguyên tắc cốt lõi
- Đẹp là quan trọng nhất, nhưng cái đẹp phải giúp người dùng hiểu nhanh và thao tác dễ.
- Dữ liệu thật, hierarchy, state và accessibility luôn đi trước hiệu ứng hoặc screenshot đẹp.
- Không thêm chữ, tag, badge, container, icon hoặc hiệu ứng nếu không giúp đọc, hiểu, scan, thao tác hoặc ra quyết định.
- UI phải chịu được dữ liệu thiếu: ảnh lỗi, title dài, metadata trống, ít/nhiều item, loading, empty và error.

## Cấu trúc và naming
- Tổ chức theo cấu trúc quen thuộc: `src/components`, `src/pages`, `src/services`, `src/utils`, `assets`, `styles`, `tests`, `docs`, `logs`, `public`.
- Tên biến, hàm, class/component phải rõ nghĩa; dùng camelCase cho biến/hàm, PascalCase cho class/component.
- Boolean dùng tiền tố `is`, `has`, `can`; event handler dùng tiền tố `handle`.
- Tránh viết tắt khó hiểu.

## Code quality
- Code phải sạch, dễ đọc, dễ bảo trì, có test và linter phù hợp.
- Tuân thủ SOLID/design pattern khi thật sự cần, không tạo abstraction thừa.
- Tối ưu hiệu suất bằng lazy loading, code splitting và kỹ thuật phù hợp với dự án.
- Đảm bảo bảo mật: không lưu secret trong mã nguồn, xử lý dữ liệu người dùng an toàn, dùng HTTPS khi áp dụng.
- Đảm bảo browser compatibility, accessibility và quy định như GDPR/HIPAA nếu dự án yêu cầu.
- Cập nhật tài liệu kỹ thuật khi có thay đổi quan trọng.

## Kiến trúc và vận hành
- Chọn framework/công nghệ theo nhu cầu thật của sản phẩm, ưu tiên khả năng mở rộng và bảo trì.
- Ứng dụng cần chịu lỗi tốt, có monitoring/logging cần thiết và cơ chế cleanup logs/dữ liệu tạm để tránh đầy ổ cứng hoặc giảm hiệu suất.

## Layout và responsive
- Layout phải dẫn mắt, làm rõ thứ tự ưu tiên và có một điểm bắt đầu rõ: hero, title, search, data summary hoặc action chính.
- Tận dụng grid nhưng không biến trang thành các khối/container xếp chồng quê mùa; UI phải hiện đại, sang trọng, chuẩn UI/UX và sẵn sàng production.
- Spacing dùng để nhóm thông tin; container chỉ dùng khi có lý do rõ, nếu làm UI nặng/thô thì bỏ.
- Desktop/tablet/mobile phải có xử lý riêng: desktop tận dụng grid rộng, tablet giảm density/gom action, mobile một cột rõ, font/spacing/card height gọn và fit màn hình.
- Mobile/iPad phải kiểm kỹ thanh search, filter, navbar, tab và action: không bị trình duyệt che, không tràn safe-area, không chiếm quá nhiều chiều cao và vẫn dễ bấm.
- Luôn ưu tiên dùng icon cho navbar, tab, filter, action để tiết kiệm space và tăng tốc độ scan, nhưng icon phải có nghĩa và không thay thế text khi gây khó hiểu.
- Thanh scroll phải hợp visual của web, không thô/lệch màu; vùng scroll ngang/dọc phải rõ, mượt và không làm layout nhảy.

## Content và typography
- Text phải ngắn, rõ, có thông tin thật; bỏ câu chung chung, phóng đại hoặc chỉ để lấp đầy UI.
- Heading định vị màn hình; lead text chỉ dùng khi bổ sung ý heading chưa nói.
- Metadata, label, tag, category chỉ giữ khi giúp scan, so sánh, filter hoặc ra quyết định.
- Card title phải nổi bật hơn metadata/badge; body/summary trả lời đây là gì, vì sao quan trọng, người dùng làm gì tiếp.
- Font scale phải tinh tế theo breakpoint; tránh `vw` quá mạnh làm chữ mobile phình, text nhỏ ưu tiên readability.
- Màn nhỏ phải giảm font size, line-height, spacing và heading scale có chủ đích; không bê nguyên desktop xuống mobile/iPad.

## Card, list, search/filter
- Card cần form ổn định, dễ scan, có điểm đọc chính, metadata phụ và action rõ; ưu tiên tỷ lệ 16/9 chữ nhật ngang khi phù hợp.
- Media/banner cần tỷ lệ cố định, crop/fade hòa vào hệ nền và luôn có fallback visual cùng hệ thiết kế.
- Không để broken image, empty card hoặc container rỗng phá layout.
- Action chính/phụ phải khác priority; CTA nổi rõ, link phụ không tranh spotlight.
- Search/filter là công cụ thao tác, không phải hero thứ hai: gọn, focus rõ, search trước filter phụ sau, desktop cùng hàng và mobile compact.
- Trên mobile/iPad, search phải dễ nhập, không bị keyboard/browser UI che, không auto zoom do font quá nhỏ và có clear/cancel state khi phù hợp.
- Trang list sản phẩm/list dữ liệu phải có search/filter, card rõ và banner; nếu chưa có banner thì tạo ảnh phù hợp.

## Visual style
- Style phải xuất phát từ sản phẩm: người dùng là ai, cần tin điều gì, đọc gì và hành động gì.
- Mood theo ngữ cảnh: profile cần bằng chứng, dashboard cần density/state rõ, landing cần narrative/CTA/trust signal, tool nội bộ cần thao tác nhanh, settings cần sắp xếp dễ hiểu.
- Giao diện phải gọn gàng, tiện lợi, tối ưu trên màn hình và dễ dùng.
- Chọn motif đa dạng nhưng nhất quán: grid, card, editorial spacing, glass, line art, imagery, v.v.
- Glass, shadow, radius, border, icon, background animation phải cùng một hệ visual và có lý do sử dụng.
- Tránh neon/glow quá tay, badge/tag dày đặc, overlay ảnh quá mạnh, text trong visual nếu không giúp hiểu nội dung.

## Màu sắc
- Màu phải được lựa chọn và phối từ đen, xanh lá, xanh dương, tím, hồng đen; dùng để tạo hierarchy, trạng thái, dẫn mắt và hỗ trợ trải nghiệm.
- Light mode và dark mode cần palette riêng; dark mode không đồng nghĩa neon, light mode không được bạc màu hoặc xám xanh bẩn.
- Background nên có chiều sâu bằng gradient, texture, grid/caro mờ, radial tiết chế hoặc animation nhẹ; tránh nền đơn sắc phẳng và đốm glow rối.
- Surface/card/fallback/ảnh phải cùng hệ màu, tách nền bằng contrast, border, shadow vừa đủ.
- CTA chính nổi hơn link phụ; error/success/warning/focus/hover đủ contrast và dễ phân biệt.

## Interaction, scroll và accessibility
- Người dùng phải nhận ra được cái gì bấm được, đang active, đang lỗi, đang loading và điều gì vừa thay đổi.
- Icon-only action phải có accessible name (`aria-label`, `title` khi phù hợp), hit area đủ và focus state rõ.
- State active/selected/focused không chỉ dựa vào màu; focus không được bị xóa khi custom style.
- Motion nhẹ, ngắn, có mục đích và tôn trọng `prefers-reduced-motion`; không dùng motion/glow chỉ để khoe hiệu ứng.
- Khi scroll phải smooth, không giật, không lock sai, không gây layout shift; anchor/section scroll cần offset đúng với header sticky.
- Có cơ chế load scene/section hợp lý cho trang nặng: skeleton, lazy render, prefetch đúng mức, image priority rõ và fallback không làm trắng màn.
- Đảm bảo không có độ trễ web thấy rõ: click/tap phản hồi nhanh, input không lag, hover/focus mượt, animation không block main thread.
- Ưu tiên semantic HTML trước ARIA phức tạp; decorative image/canvas dùng `aria-hidden="true"` hoặc `alt=""` đúng ngữ cảnh.
- Form/search/filter cần label hoặc accessible name; contact/action external dùng href đúng loại (`mailto:`, `tel:`, URL hợp lệ).
- QR hoặc mã liên hệ phải là dữ liệu thật và có link tương ứng, không dùng QR giả để trang trí.

## Checklist hoàn thành
- Màn hình đẹp, rõ hierarchy, hiểu được trong vài giây và biết thao tác tiếp theo.
- Dữ liệu thiếu, text dài, ảnh lỗi, loading/empty/error không làm UI vỡ.
- Action chính dễ thấy, dễ bấm, keyboard focus được và đủ contrast ở light/dark.
- Search/filter/card/list responsive tốt trên desktop, tablet, mobile; không bị browser UI/keyboard/safe-area che.
- Scroll, scene loading, input và animation mượt, không có độ trễ thấy rõ.
- Không còn chi tiết trang trí rỗng hoặc lặp nghĩa làm UI nhiễu.
