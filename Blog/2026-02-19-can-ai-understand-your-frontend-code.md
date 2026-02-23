---
title: 你的前端代码，AI 能读懂吗？
slug: can-ai-understand-your-frontend-code
---
# 你的前端代码，AI 能读懂吗？
> [!TIP]
>
> *<small>本文约 1681 字，预估阅读时间 约 8 分钟。</small>*

> 在传统 Web 时代，网页是给"人"看的；
>
> 在 AI Agent 时代，网页除了要给"人"看，还要能被"机器"理解。

随着越来越多 AI Agent（OpenClaw、Manus、OpenAI Operator、Claude Computer Use）开始能够直接操作 Web 页面，有一个问题愈发值得考虑：**你的前端代码，AI 能读懂吗？**

本文旨在从技术角度阐述以下三件事：

1. AI Agent 是如何理解并操作 Web 页面的
2. 为什么现代前端组件对 AI 来说常常不够友好
3. 给前端开发者的一些启示

***

## 1. AI Agent 是如何理解并操作 Web 页面的

很多人以为 AI 操作 Web 页面的流程是：

```
看屏幕截图 → 视觉识别 → 点击
```

这种方式的确存在，但更普遍采用的方式是：

```
浏览器 → DOM → Accessibility Tree → LLM → 行为规划 → 自动化执行
```

AI 主要**通过语义结构，而非像素**来理解页面。

### Accessibility Tree：AI 真正看到的内容

浏览器内部有三个核心树结构：

| 树                  | 用途              | 内容         |
| ------------------ | --------------- | ---------- |
| DOM Tree           | JS 操作和事件处理      | 原始 HTML 结构 |
| Render Tree        | 视觉渲染和布局计算       | 布局像素       |
| Accessibility Tree | 辅助设备 / 自动化 / AI | 页面含义       |

**AI 依赖的正是第三棵树：Accessibility Tree（可访问性树）**

以下面这段 HTML 为例：

```html
<label>Email</label>
<input type="email">
<button>Login</button>
```

浏览器会生成如下 Accessibility Tree：

```
textbox "Email"
button "Login"
```

基于这一结果，AI 便可推断出这是一个登录流程，需要填写邮箱地址并点击登录按钮。

### 语义组件决定了 AI 能否正确理解 Web 页面的"操作意图"

来看一个登录页面的两种写法。

#### 非语义写法（视觉组件）

```html
<div class="login">
  <div>Email</div>
  <input>
  <div>Password</div>
  <input>
  <div class="btn">Login</div>
</div>
```

浏览器生成的 Accessibility Tree 如下：

```
generic "Email"
textbox ""
generic "Password"
textbox ""
generic "Login"
```

对 AI 来说：只是几个盒子和文本 —— 不知道能做什么。

#### 语义写法（语义组件）

```html
<form>
  <label>Email</label>
  <input type="email">
  <label>Password</label>
  <input type="password">
  <button>Login</button>
</form>
```

浏览器生成的 Accessibility Tree 如下：

```
form
  textbox "Email"
  password "Password"
  button "Login"
```

现在 AI 可以推理，这是一个登录用的表单，有一个邮箱输入框、一个密码输入框以及一个登录按钮，于是生成以下执行计划：

```
Fill "Email"
Fill "Password"
Click "Login"
```

> 上述两种 Web 页面的写法对人类而言从浏览器看过去完全一致，但对 AI 来说却大不相同。

### 插个话题：为什么 AI Agent 更常用 Playwright 而不是 Selenium

目前几乎所有 Browser Agent 都基于 Playwright。

#### 1. 控制层级不同

**Selenium：在浏览器外部遥控**

```
Agent → WebDriver → 浏览器
```

浏览器对 Selenium 来说是一个"黑盒网页播放器"。

它能做的事本质是：

```
找到元素 → 点击
```

但不知道：

* 元素是否被遮挡
* 是否真的可点击
* 是否正在加载
* 页面是否稳定
* 用户能不能操作

**Playwright：直接调用浏览器内部 API**

```
Agent → DevTools Protocol → 浏览器内部状态
```

Playwright 直接读取浏览器运行时：

* DOM
* Layout
* 可见性
* 可访问性树
* 网络状态
* 动画状态

所以它能回答一个关键问题：

> 现在用户能不能操作这个元素？

Agent 极度依赖这个能力。

#### 2. Agent 依赖"语义操作"，不是"选择器操作"

Agent 的目标不是执行脚本：

```javascript
click('#login-btn')
```

而是执行意图：

```
click the login button
```

要做到这一点必须用：

* Accessibility Tree
* role
* name
* 可交互状态

Playwright 原生支持：

```javascript
getByRole('button', { name: 'Login' })
```

而 Selenium 基本没有这个层级的能力（只能靠 XPath / CSS 猜）。

| 能力                    | Selenium                   | Playwright             |
| ----------------------- | -------------------------- | ---------------------- |
| 控制模型                | WebDriver 协议（浏览器外） | 浏览器内 DevTools 协议 |
| 获取 Accessibility Tree | 困难                       | 原生支持               |
| 获取布局/渲染信息       | 弱                         | 强                     |
| 等待机制                | 手写实现                   | 自动实现               |
| 状态观察                | 几乎没有                   | 完整                   |
| 对 AI 友好程度          | 低                         | 高                     |

**AI Agent 需要理解页面的状态，而不只是执行点击操作。**

***

## 2. 为什么很多前端框架生成的组件对 AI 来说不够友好

现代前端开发存在一个普遍现象：**UI 看起来越高级，对 AI 越难读。**

### 例 1：自定义按钮组件

很多系统这样写：

```html
<div class="ant-btn">Submit</div>
```

视觉：完全正确。语义：完全丢失。

Accessibility Tree 显示：

```
generic "Submit"
```

AI 不知道它是不是按钮。

### 例 2：自定义 Select 组件（最常见的灾难）

React/Vue UI 框架常见实现：

```html
<div class="select">
  <div class="value">中国</div>
  <div class="dropdown">
    <div class="option">中国</div>
    <div class="option">美国</div>
  </div>
</div>
```

人类看到下拉框。AI 看到一堆 div。

正确语义应该接近：

```html
<select>
  <option>中国</option>
  <option>美国</option>
</select>
```

否则 Agent 无法执行 `Select country = 中国`，它甚至不知道这是个可选项控件。

### 例 3：富文本编辑器

```html
<div contenteditable="true"></div>
```

AI 无法判断：是否是输入框？是否需要回车提交？是否支持快捷键？是否需要失焦触发校验？

### 例 4：缺少 form 容器

```html
<div class="form">
  ...
</div>
```

AI 无法识别任务边界，无法判断哪些输入字段属于同一组操作。

### 本质问题：前端在"抹掉语义"

现代前端框架大量使用 `div + css + js = 一切`。这对浏览器没问题，对人类没问题，对 AI 是灾难。

**AI 不理解视觉样式，只理解交互语义。**

***

## 3. 带给前端开发者的启示

AI Agent 的出现，相当于 Web 从 Human Interface 变成了 Human && Machine Interface，这会改变前端开发方式的最佳实践。

### 原则 1：优先使用原生语义标签

永远优先用 `<button>`、`<input>`、`<label>`、`<form>`、`<select>`，而不是 `<div role="button">`（除非必要）。

语义标签就是免费的 API 文档。

### 原则 2：当你必须自定义组件时，补齐 ARIA 语义

例如：

```html
<div role="button" aria-label="提交订单" tabindex="0"></div>
```

这不仅有助于 AI 理解，也提升了无障碍访问体验。

参考规范：[WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

### 原则 3：前端测试标准将改变

未来的 E2E 测试不再是：

```javascript
cy.get('.btn-primary')
```

而是：

```javascript
getByRole('button', { name: '提交订单' })
```

> 旧 E2E 测试在检查“前端有没有按原样式写代码”
> 新 E2E 测试在检查“用户是否还能完成任务”

而 AI Agent 就是那个“真正的用户”。

### 原则 4：语义化将成为 SEO 之后的新刚需

曾经前端语义化是为了 SEO 和无障碍性（Accessibility），现在增加了一个新驱动力：**可被 AI 使用（AI Usability）**。

今后 SaaS 的竞争力之一会变成：**你的系统是否可被 AI Agent 自动操作**，否则将无法接入未来的 AI 自动化办公流。

***

## 总结

> 人类通过视觉理解网页，AI 通过语义理解网页。

> 过去我们写代码是给浏览器解析，今后我们写代码是给 AI 理解，前端语义化组件的真正意义不是为了规范，而是为了能让你的产品**被机器员工正确使用**。

