# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

始终使用简体中文进行回复。包括解释、代码注释、错误提示等。

## 项目文档

设计文档位于 `docs/` 目录：

- `docs/01-系统设计文档.md` — 架构图、模块划分、RBAC权限模型、部署方案
- `docs/02-数据库设计文档.md` — 全部建表SQL、字段说明、索引策略、ER关系
- `docs/03-API接口文档.md` — RESTful接口定义、请求响应示例、错误码规范

## 技术栈

Python Django 4.2 LTS + Django REST Framework + Vue 3 + MySQL 8.0 + Redis + Celery
