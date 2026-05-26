---
name: readme-style
description: "Style guide cho README dạng docs hub của repo này."
argument-hint: "README task"
user-invocable: true
---

# README Style Guide

Áp dụng khi tạo hoặc cập nhật README, banner, badge, quick navigation, repo map, kiến trúc, Mermaid diagram, docs index hoặc accuracy notes.

Readme luôn có thời gian cập nhật mới nhất, có link tới changelog và release metadata nếu có, và có link tới docs index nếu repo có nhiều doc. Readme phải khớp với file hiện có trong repo, không để link chết hoặc path không tồn tại. Readme nên ngắn gọn, dễ scan, trung thực kỹ thuật hơn quảng cáo, và có link tới docs/changelog/release metadata khi cần.

Có 'dev by ambrouse' ở cuối trang.

## Mục Tiêu

- README là trang tổng quan kỹ thuật, giúp người đọc hiểu repo làm gì, vào đâu để dùng/sửa, và verify thế nào.
- Ưu tiên trung thực kỹ thuật hơn quảng cáo.
- Nội dung ngắn, dễ scan, có link tới docs/changelog/release metadata khi cần.

## Bố Cục Khuyến Nghị

1. Hero căn giữa: tên repo, tagline, badge, navigation.
2. Tổng quan: repo giải quyết việc gì và các runtime root.
3. Skill matrix hoặc module matrix.
4. Workflow bằng Mermaid nếu có nhiều bước.
5. Quick start hoặc validation command chạy thật.
6. Repository map.
7. Docs index.
8. Operating notes và accuracy notes.

## Ngôn Ngữ

- Viết tiếng Việt có dấu nếu repo đang dùng tiếng Việt.
- Câu ngắn, rõ, tránh phóng đại và tránh mô tả feature chưa có.
- Khi một nội dung là giả định, tùy chọn hoặc chưa verify, ghi rõ.

## GitHub Markdown

- Có thể dùng `<div align="center">` cho hero.
- Dùng badge `for-the-badge` vừa đủ, không quá nhiều.
- Dùng bảng Markdown cho matrix và repo map ngắn.
- Dùng Mermaid để mô tả flow thay vì ảnh tự chế.

## Accuracy Notes

- README phải khớp file hiện có trong repo.
- Khi thêm/xóa skill, workflow, docs folder hoặc version metadata, cập nhật README cùng task.
- Không để README chứa ký tự lỗi mã hóa, link chết hoặc path không tồn tại.
