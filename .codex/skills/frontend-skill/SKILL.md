---
name: frontend-skill
description: "Quy tắc bắt buộc khi thiết kế, viết và review code frontend."
argument-hint: "frontend task"
user-invocable: true
---

# Frontend Skill

Áp dụng khi task chạm UI, layout, state, route, form, API client, accessibility, responsive hoặc trải nghiệm người dùng.

## Nguyên Tắc

- Xây dựng màn hình dùng được ngay, không làm landing page nếu user yêu cầu app/tool/game.
- Bám design system, component pattern và spacing hiện có trước khi tạo style mới.
- UI phải rõ hierarchy, dễ scan, không lạm dụng card lồng card, gradient, blob trang trí hoặc text giải thích cách dùng ngay trong app.
- Text phải fit trên mobile/desktop, không chồng lên nhau, không tràn khỏi button/card/panel.
- Dùng control quen thuộc: icon button cho tool, switch/checkbox cho boolean, slider/input cho số, tab cho view, menu cho option set.
- Dùng icon từ thư viện sẵn có, ưu tiên `lucide` khi repo đã dùng.

## Layout Và Responsive

- Đặt dimension ổn định cho toolbar, grid, board, tile, counter và button để hover/loading/dynamic text không làm layout nhảy.
- Không scale font bằng viewport width; giữ letter spacing bằng `0` trừ khi design system yêu cầu khác.
- Kiểm tra empty/loading/error/long text/image error vì các state này thường làm UI vỡ.
- Mobile phải xét safe area, keyboard, browser chrome, scroll và hit target.
- Dashboard/operational tool nên yên tĩnh, dày thông tin vừa đủ, ưu tiên scan và thao tác lặp lại.

## State Và API

- Loading, empty, error, retry và optimistic update phải có hành vi rõ.
- API client cần handle timeout/error/network offline theo pattern repo.
- Không để dữ liệu stale hoặc race condition làm UI hiển thị sai sau filter/search/pagination.

## Verification

- Khi có UI change, chạy app thật và kiểm tra bằng browser nếu môi trường cho phép.
- Kiểm tra responsive desktop/mobile, focus state, keyboard navigation, contrast và text overflow.
- Nếu không thể mở app/browser, ghi rõ blocker và rủi ro còn lại.
