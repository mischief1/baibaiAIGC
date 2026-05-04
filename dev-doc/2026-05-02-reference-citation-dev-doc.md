# 参考文献功能开发文档

## 1. 文档目的

本文档用于指导 `baibaiAIGC` 项目新增“添加参考文献”独立功能的设计与开发。该功能与现有“降 AI”能力完全解耦，作为新的文档处理流水线存在。

本文档覆盖：

- 产品目标与边界
- 核心流程
- 后端模块划分
- 前端页面设计
- 数据模型
- API 设计
- Browser MCP + 知网接入边界
- 风控与安全要求
- 测试与验收标准

## 2. 功能定义

### 2.1 目标

用户上传一篇 `docx/txt` 论文后，系统能够：

1. 自动分析全文结构
2. 自动识别适合添加引用的句子或论述点
3. 自动估算适合的参考文献数量
4. 支持用户指定中文文献数和英文文献数
5. 联网检索真实可信的英文和中文参考文献
6. 在正文对应句子位置插入 `[1]`、`[2]` 这类引用标记
7. 在文末生成仅包含正文已实际引用条目的参考文献列表
8. 导出带引用的新文档

### 2.2 非目标

本版本不做以下事情：

1. 不与现有降 AI round/chunk 流程合并
2. 不做大规模自动抓取知网
3. 不自动下载论文全文
4. 不保存知网账号密码
5. 不提供绕过风控、验证码、权限校验的能力
6. 不在第一版支持用户逐句手工编辑引用绑定关系

## 3. 产品原则

### 3.1 独立功能原则

参考文献功能必须是独立工作台，不依赖现有“降 AI”流程，也不复用其 round 状态机。

### 3.2 真实可信原则

参考文献不能由模型虚构。所有最终输出条目必须来自真实检索结果。

### 3.3 少搜原则

对于长文不能逐句搜索，必须先做全文分析、候选句筛选和主题聚类，再执行有限次数检索。

### 3.4 人工在场原则

中文知网检索必须由用户手动登录并确认候选文献，系统只能辅助，不得演化成自动抓取器。

### 3.5 句级引用原则

引用编号应尽量插入对应句子后，而不是简单挂在段尾。

## 4. 总体架构

功能采用双轨半自动方案：

- 英文文献：后端 API 自动检索
- 中文文献：Browser MCP 辅助知网检索，用户登录并确认候选

最终由系统统一完成：

- 候选句选择
- 主题聚类
- 文献绑定
- 编号排序
- `[x]` 插入
- 文末参考文献生成

### 4.1 核心流程

1. 用户上传文档
2. 系统解析正文
3. 系统分析全文并给出建议：
   - 建议总文献数
   - 建议中文/英文数量
   - 建议引用位置数
   - 建议搜索主题簇
4. 用户确认中文/英文目标条数
5. 系统自动检索英文候选
6. 系统启动知网辅助检索
7. 用户登录知网并确认中文候选
8. 系统合并候选并自动生成句级绑定
9. 系统插入正文引用并生成参考文献列表
10. 用户预览并导出结果

## 5. 长文处理策略

### 5.1 为什么不能逐句搜索

几万字论文中，并非每一句都需要引用。若逐句提词并搜索：

- 搜索次数过多
- 检索成本高
- 知网风险高
- 结果大量重复
- 绑定结果噪声大

因此必须先做“引文需求识别”。

### 5.2 引文需求识别

系统为句子打 `citation_need_score`，重点识别：

- 研究背景中的事实性描述
- 文献综述中的归纳表达
- 理论、定义、方法来源
- 数据、结论、比较性判断
- 具有“已有研究表明”“学者认为”“根据某理论”等信号的句子

### 5.3 主题聚类

高分句不直接一对一搜索，而是按主题聚合为有限数量的主题簇。

建议限制：

- 候选引文句数：30 到 60
- 主题簇数量：10 到 20
- 中文检索主题簇：最多 10
- 每个主题簇仅保留少量核心候选

### 5.4 文献数量估算

系统先基于以下信息给出建议条数：

- 总字数
- 章节类型
- 高引文需求句数量
- 主题簇数量

再允许用户输入最终目标：

- 中文文献数
- 英文文献数

## 6. 真实来源策略

### 6.1 英文文献

英文文献来源：

- `OpenAlex`
- `Crossref`

最终文献至少包含：

- 标题
- 作者
- 年份
- 来源
- DOI 或可回溯主键

### 6.2 中文文献

中文文献来源：

- 知网浏览器辅助检索

最终文献至少包含：

- 标题
- 作者
- 年份
- 来源
- 检索来源信息

中文候选进入最终结果前必须经过用户确认。

## 7. Browser MCP + 知网设计

### 7.1 功能角色

Browser MCP 在本功能中只负责：

1. 打开知网页面
2. 支持用户在浏览器中登录
3. 辅助输入搜索词
4. 读取当前页少量候选结果
5. 把用户确认过的候选文献回传给系统

### 7.2 不允许的行为

Browser MCP 不允许用于：

1. 连续翻页批量采集
2. 后台无人值守长时间抓取
3. 批量下载全文
4. 规避验证码
5. 伪装或隐藏自动化行为

### 7.3 推荐检索节奏

每次任务：

1. 一次只处理一个主题簇
2. 每个主题簇默认只看前 1 页
3. 特殊情况下允许用户主动继续到第 2 页
4. 候选确认后再进入下一主题簇

### 7.4 登录与敏感信息

必须满足：

1. 用户自行登录知网
2. 系统不采集、不存储、不回显账号密码
3. 登录态仅存在于当前浏览器会话
4. 允许任务结束后清理会话

## 8. 后端设计

### 8.1 目录建议

建议在 `scripts/` 下新增参考文献相关模块：

- `reference_models.py`
- `reference_document.py`
- `reference_analysis.py`
- `reference_search_english.py`
- `reference_search_cn.py`
- `reference_binding.py`
- `reference_export.py`
- `reference_records.py`
- `reference_service.py`
- `reference_pipeline.py`

### 8.2 模块职责

#### `scripts/reference_models.py`

定义功能专属数据模型：

- `ReferenceJob`
- `ReferenceDocument`
- `ParagraphNode`
- `SentenceNode`
- `SentenceCandidate`
- `TopicCluster`
- `ReferenceCandidate`
- `CitationBinding`
- `ReferencePreview`
- `ReferenceApplyResult`

#### `scripts/reference_document.py`

负责文档结构解析：

- 读取 `docx/txt`
- 切分段落
- 切分句子
- 识别章节标题
- 排除已有参考文献区

#### `scripts/reference_analysis.py`

负责全文分析：

- 句级打分
- 候选句筛选
- 主题聚类
- 检索词生成
- 建议条数估算

#### `scripts/reference_search_english.py`

负责英文候选文献获取：

- OpenAlex 检索
- Crossref 校验
- 元数据补全
- 去重
- 打可信度分

#### `scripts/reference_search_cn.py`

负责中文候选结果归档：

- 接收 Browser MCP 流程中确认的候选
- 标准化字段
- 标记 `userConfirmed`
- 输出统一候选结构

#### `scripts/reference_binding.py`

负责句级绑定：

- 将候选文献映射到高分句
- 允许一篇文献绑定多个相近句子
- 限制同段引用密度
- 生成编号顺序

#### `scripts/reference_export.py`

负责结果写回：

- 把 `[x]` 插入句子
- 生成参考文献区
- 输出 txt
- 输出 docx

#### `scripts/reference_records.py`

负责任务历史：

- 保存任务状态
- 保存候选文献信息
- 保存最终导出路径

#### `scripts/reference_service.py`

负责 API 业务编排：

- 新建任务
- 分析全文
- 保存用户配置
- 检索英文文献
- 接收中文候选
- 生成绑定
- 预览
- 导出

#### `scripts/reference_pipeline.py`

负责高层流水线控制：

- 串联全文分析、候选生成、绑定和导出
- 统一任务状态流转

## 9. 数据模型建议

### 9.1 `ReferenceJob`

- `jobId`
- `sourcePath`
- `sourceKind`
- `status`
- `analysisStatus`
- `englishSearchStatus`
- `cnSearchStatus`
- `bindingStatus`
- `exportStatus`
- `targetChineseCount`
- `targetEnglishCount`
- `createdAt`
- `updatedAt`

### 9.2 `SentenceCandidate`

- `sentenceId`
- `paragraphIndex`
- `sentenceIndex`
- `sectionTitle`
- `text`
- `citationNeedScore`
- `topicClusterId`
- `selected`

### 9.3 `TopicCluster`

- `topicClusterId`
- `label`
- `languagePreference`
- `queryTerms`
- `sentenceIds`
- `recommendedReferenceCount`

### 9.4 `ReferenceCandidate`

- `candidateId`
- `language`
- `title`
- `authors`
- `year`
- `source`
- `doi`
- `url`
- `abstractSnippet`
- `topicClusterId`
- `confidenceScore`
- `verified`
- `userConfirmed`

### 9.5 `CitationBinding`

- `bindingId`
- `sentenceId`
- `candidateIds`
- `bindingScore`
- `applied`

## 10. API 设计

建议在 [scripts/web_app.py](D:/code/new/baibaiAIGC/scripts/web_app.py) 中新增 `/api/reference/*` 接口组。

### 10.1 任务管理

#### `POST /api/reference/upload-document`

作用：

- 上传源文档
- 创建参考文献任务

响应建议：

- `jobId`
- `sourcePath`
- `filename`

#### `GET /api/reference/status`

作用：

- 获取任务总状态和阶段状态

#### `GET /api/reference/history`

作用：

- 获取参考文献历史任务

### 10.2 分析阶段

#### `POST /api/reference/analyze`

作用：

- 执行全文结构分析和候选句识别

返回：

- 字数
- 章节信息
- 候选引文句数
- 主题簇
- 建议中文/英文条数

#### `POST /api/reference/configure`

作用：

- 保存用户选择的中文/英文条数

### 10.3 英文检索阶段

#### `POST /api/reference/search-english`

作用：

- 批量执行英文候选检索

返回：

- 英文候选列表
- 校验状态

### 10.4 中文知网阶段

#### `POST /api/reference/start-cn-browser-session`

作用：

- 初始化知网检索会话
- 返回当前主题簇和建议检索词

#### `POST /api/reference/submit-cn-candidates`

作用：

- 提交用户确认过的中文候选文献

### 10.5 绑定与导出阶段

#### `POST /api/reference/generate-bindings`

作用：

- 基于候选文献生成句级绑定结果

#### `GET /api/reference/preview`

作用：

- 获取带引用结果的预览文本

#### `POST /api/reference/apply`

作用：

- 正式应用绑定结果
- 生成最终引用文档

#### `GET /api/reference/export`

作用：

- 导出 `txt/docx`

## 11. 前端页面设计

建议在现有 `workspace/history/result` 之外，新增一个独立“参考文献”工作台。

### 11.1 页面一：参考文献工作台

职责：

- 上传文档
- 启动分析
- 配置目标中文/英文条数

展示信息：

- 文件名
- 字数
- 章节概览
- 建议引用位置数
- 建议总条数

交互：

- 上传按钮
- 分析按钮
- 中文数量输入框
- 英文数量输入框
- 开始检索按钮

### 11.2 页面二：全文分析结果页

职责：

- 解释系统为什么推荐这些条数和位置

展示信息：

- 高引文需求句数量
- 主题簇数量
- 各章节引文密度建议
- 推荐中英文条数

### 11.3 页面三：英文候选文献页

职责：

- 展示英文候选文献

展示字段：

- 标题
- 作者
- 年份
- 来源
- DOI
- 摘要片段
- 校验状态

### 11.4 页面四：知网辅助检索页

职责：

- 引导用户登录知网并确认中文候选文献

展示内容：

- 当前主题簇
- 推荐检索词
- 检索进度
- 已确认中文候选
- 安全与合规提示

### 11.5 页面五：绑定预览页

职责：

- 展示系统自动生成的句级绑定结果

展示内容：

- 哪些句子将插入 `[x]`
- 每个编号对应哪条文献
- 某条文献支持哪些句子

第一版建议只读预览，不开放逐句手工编辑。

### 11.6 页面六：导出页

职责：

- 预览最终带引用正文
- 预览参考文献区
- 导出结果文档

## 12. 前端状态设计

建议新增独立状态树，不复用现有 round 状态：

- `referenceJob`
- `referenceAnalysis`
- `englishCandidates`
- `cnCandidates`
- `bindings`
- `referencePreview`
- `referenceExport`

## 13. 安全与风控要求

### 13.1 登录安全

1. 不采集知网账号密码
2. 不把密码传给后端
3. 不在日志中输出登录信息

### 13.2 检索频率控制

1. 每次只处理一个主题簇
2. 单次任务最多 10 个中文主题簇
3. 每个主题簇默认只查前 1 页
4. 用户主动继续时才允许第 2 页

### 13.3 中断条件

出现以下情况时立即停止自动流程：

1. 验证码
2. 登录失效
3. 风险页
4. 页面结构无法识别

### 13.4 数据最小化

只保存：

- 文献元数据
- 任务状态
- 导出结果路径

不保存：

- 账号密码
- 无关页面内容
- 批量页面快照

## 14. 测试设计

### 14.1 后端单元测试

- 文档解析
- 章节识别
- 参考文献区排除
- 候选句打分
- 主题聚类
- 条数估算
- 英文检索结果解析
- 文献去重
- 句级绑定
- 编号排序
- 文本写回

### 14.2 集成测试

- 上传到预览全链路
- 英文检索全链路
- 中文候选提交到绑定全链路
- 导出 docx

### 14.3 人工验收

重点检查：

1. 是否真的跳过已有参考文献区
2. `[x]` 是否落在句子级而不是段尾
3. 文末列表是否只包含正文实际使用的条目
4. 中文知网流程是否可控、低频、无敏感数据落盘

## 15. 验收标准

满足以下条件才可认为版本合格：

1. 可上传 `docx/txt` 并完成全文分析
2. 系统能给出建议条数
3. 英文文献来自真实来源并通过校验
4. 中文文献必须包含知网 Browser MCP 流程
5. 用户只需登录和确认候选，不必逐句手工绑定
6. 系统能自动插入句级 `[x]`
7. 文末参考文献区只包含正文已引用条目
8. 可导出 `docx`
9. 不保存知网账号密码
10. 遇到验证码或异常时能立即停止

## 16. 当前推荐的实施顺序

1. 建独立数据模型与任务记录
2. 完成文档解析与全文分析
3. 完成英文检索与校验
4. 完成句级绑定与导出
5. 接入知网 Browser MCP 辅助检索
6. 联调中文候选确认链路
7. 做整体验证与风控回归

---

这份文档对应当前确认的功能方案，可作为后续实现计划和开发拆分的基础文档。
