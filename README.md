# OmniArch-Aero｜CMAME 论文写作框架

## 仓库入口

- [英文稿 LaTeX](./cas-sc-template.tex) · [英文稿 PDF](./cas-sc-template.pdf)
- [中文稿 LaTeX](./omniarch-aero-zh/cas-sc-template_zh.tex) · [中文稿 PDF](./omniarch-aero-zh/cas-sc-template_zh.pdf)
- [项目代码和复现说明](./omniarch-aero-main/README.md) · [CAS 单栏示例](./cas-sc-sample/cas-sc-sample.pdf)

英文稿从仓库根目录用 pdfLaTeX 编译，中文稿从 `omniarch-aero-zh/` 用 XeLaTeX 编译。两份稿件均使用 BibTeX。首次编译时，先运行对应 LaTeX 引擎一次，再运行 BibTeX，最后用 LaTeX 引擎编译两次。叶片原始 CFX 数据的获取范围见[数据说明](./omniarch-aero-main/data/blade/README.md)。

**结构判断。** 保留六章，正文约 17 页。第 4 章用公开翼型基准回答“雷诺数超出训练区间后，流场和升力还能预测到什么精度”；第 5 章用工业叶片回答“低温工况的信息能解释多少高温金属温度变化，网络还修正了多少”。两个案例共享计算框架，分别训练和评价。这个结构适合展开为 CMAME 研究论文。投稿前要让读者从变量定义一路追溯到工程误差，并在实际稿件中填入同口径的结果图表。

**数学主线。** 翼型从无量纲动量平衡引出输入、输出尺度，最后从场量恢复升力。叶片从温度相似换算出发，建立逐节点先验和残差目标，最后把误差换算成 K。OmniArch 作为预训练主干，在同一张流程图中说明其位置和迁移范围。原论文 §3.1.2 用加权时间更新和时序掩码解释自己的设计。本文采用稳态工况的网格编码与空间查询，只展开本文实际用到的计算关系。[OmniArch 原文 §3.1](https://arxiv.org/html/2402.16014#S3.SS1)

### 对照五篇 CMAME 例文后的取舍

| 例文与 PDF 页码 | 值得借鉴的数学写法 | 本文如何采用 |
|---|---|---|
| [空化多保真代理模型](https://doi.org/10.1016/j.cma.2026.119558)，pp. 3、6–10、19 | 从壁面载荷定义转入输出变换、异方差观测和变分推断，最后用压力和概率指标评价。其方法章有六个小节，各自对应一项具体建模步骤。 | 借用“公开基准—工程应用”的顺序。将继承的网络组件合并，篇幅留给相似变量与温度先验。 |
| [热学 VDMN](https://doi.org/10.1016/j.cma.2026.119563)，pp. 3–6、14–17 | 作者从热流与温度梯度关系写到两相层合材料的有效热导，再用雅可比矩阵传播不确定性。这些公式直接进入结果解释。 | 借鉴从模型输出推到工程量的写法。在叶片结果中用同一个温差尺度解释无量纲误差和金属温度误差。 |
| [PGD 散射模型](https://doi.org/10.1016/j.cma.2026.119546)，pp. 3、5、10 | 从 Helmholtz 问题进入参数化弱式与分离表示，算例再用散射宽度量化解的表现。 | 将翼型的预测场与升力积分分别定义，给读者一条从场误差到设计量的计算路径。 |
| [Cahn–Hilliard 变分方法](https://doi.org/10.1016/j.cma.2026.119554)，pp. 2–4、14 | 通量作为未知量改变了变分原理和离散问题，因此作者详细写出相应的强式与弱式。 | 本文改变的是学习变量与目标，推导集中在变换、拟合和逆变换。CFD 离散属于参考数据生成，可引用其来源。 |
| [ALE 自由边界方法](https://doi.org/10.1016/j.cma.2026.119572)，pp. 6、9、12、17 | 离散重力项、能量关系和数值试验前后对应，因此守恒性值得独立成节。 | 采用同样的对应关系：为相似特化给出配置对照，为叶片残差给出先验基线。本文的验证依据是数值结果。 |

**小节数与页数。** 原框架有 17 个编号小节。新版将网格分块、主干、解码和训练放入同一方法小节，将评价指标放回使用该指标的算例，将局限放入各章结果解释，共保留 11 个编号小节。引言和结论连续行文。下表是本稿的工作预算，按 CAS 单栏成稿计算，图、表、公式计入所在小节。摘要、参考文献和附录另计。

| 章 | 小节及其页数 | 章合计 |
|---|---|---:|
| 1 引言 | 连续行文 2.00 | 2.00 |
| 2 物理问题与外推任务 | 2.1 翼型流动与雷诺数外推 1.00；2.2 冷却叶片与温度工况外推 1.00 | 2.00 |
| 3 相似特化方法 | 3.1 翼型流场的相似变换 1.25；3.2 叶片温度先验与残差重构 1.50；3.3 网格到场的映射与训练 1.25 | 4.00 |
| 4 AirfRANS 雷诺数外推验证 | 4.1 基准划分与比较设置 0.75；4.2 从流场到升力的误差 2.00；4.3 外推性能分析与推理耗时 1.25 | 4.00 |
| 5 冷却涡轮叶片温度外推与讨论 | 5.1 工程算例与对照方法 1.00；5.2 金属温度场与热点误差 1.75；5.3 先验贡献与适用范围 1.25 | 4.00 |
| 6 结论 | 连续行文 1.00 | 1.00 |
| **正文** | **11 个编号小节** | **17.00** |

**读法。** 每节从第 1 点开始，编号为建议的写作顺序。P 链接指向项目实现和项目已确认的结果，R 链接指向已核实的外部文献。标为“写作建议”的内容用于组织论证。居中图表题下给出图面或表列及其制作依据。行间式可以直接迁入 TeX，正式稿用 equation 或 align 环境编号。

## 1、引言（Introduction）｜约 2 页

1. **工程动机｜外部文献。** 从“一种设计、多个运行条件”写起。先解释流场、气动力和金属温度在设计评估中的作用，再说明逐工况求解为何产生计算负担。用参数化降阶与流体机器学习综述支持这一背景，具体算例时间留到第 4 章。[R1](#r1)、[R2](#r2)、[R6](#r6)
2. **已有方法与研究问题｜外部文献＋项目。** 用一段串联 FNO、DeepONet 的解算子观点，Transolver 对复杂几何的处理，以及 OmniArch 的预训练思路。随后把问题缩小到本文情形：获得新几何或新工况的描述后，模型能否预测训练雷诺数或温度范围外的场？[R7](#r7)、[R8](#r8)、[R14](#r14)、[R15](#r15)、[P1](#p1)
3. **无量纲学习的依据｜外部文献＋项目。** 从 Buckingham 的相似理论出发，先交代 Bakarji 等怎样从数据识别无量纲群，再交代 Oppenheimer 等怎样用无量纲变量学习跨尺度关系并检验外推。用来流速度的例子落到本文：速度与运动压力分别按 $U_\infty$ 和 $U_\infty^2$ 缩放，流场仍随 $Re$ 变化。冷却叶片同样可以先换算温差尺度，再估计无量纲温度随工况的变化。[R3](#r3)、[R16](#r16)、[R17](#r17)、[R18](#r18)、[R20](#r20)、[P2](#p2)、[P3](#p3)
4. **本文贡献｜项目。** 将创新落在非结构网格场预测的具体设计。用 OmniArch 的部分预训练参数初始化主干，以空间块编码和查询点解码连接不规则网格与预测场。翼型采用预先定义的相似变量表示流场，叶片在逐节点相似温度先验上学习残差。两个任务分别训练，并用各自的对照量化外推效果。[R14](#r14)、[R16](#r16)、[R17](#r17)、[P2](#p2)、[P3](#p3)、[P4](#p4)、[P5](#p5)
5. **评价路线｜项目。** 段末给出两个可由结果回答的问题：在 AirfRANS 上，这套配置对流场和升力预测有多大改善？在固定叶片上，简单相似换算、温度先验和网络修正各解释多少高温误差？整段控制在数句，主比较表分别置于第 4、5 章。[P1](#p1)、[P8](#p8)

## 2、物理问题与外推任务（Problem statement）｜约 2 页

### 2.1、翼型流动与雷诺数外推｜1.00 页

1. **参考物理问题｜外部文献＋项目。** 定义二维稳态不可压缩翼型绕流，给出弦长 $L$、来流速度 $U_\infty$、攻角 $\alpha$ 和运动黏度 $\nu$。解释参照数据来自 RANS 计算。在定密度、定运动黏度且忽略体力的假设下，用下式说明雷诺数进入平均动量平衡的位置。这里保留雷诺应力的一般形式，具体闭合与边界条件引向 AirfRANS 原文。[R4](#r4)、[R13](#r13)、[P2](#p2)

$$
\begin{aligned}
\nabla^*\!\cdot\mathbf u^*&=0,\\
(\mathbf u^*\!\cdot\nabla^*)\mathbf u^*
&=-\nabla^*p^*+Re^{-1}\nabla^{*2}\mathbf u^*
  -\nabla^*\!\cdot\mathbf R^*,\qquad Re=\frac{U_\infty L}{\nu}.
\end{aligned}
\tag{1}
$$

取 $\mathbf x^*=\mathbf x/L$、$\mathbf u^*=\overline{\mathbf u}/U_\infty$、$p^*=(\overline p-p_{\rm ref})/(\rho U_\infty^2)$ 和 $\mathbf R^*=\overline{\mathbf u'\otimes\mathbf u'}/U_\infty^2$。据此指出，去除速度和压力的量纲尺度后，$Re$ 仍影响解的结构，这正是外推试验需要回答的问题。

2. **任务定义｜项目。** 指明输入为几何和来流工况，节点输出为 $(u,v,p_{\rm kin},\nu_t)$，其中 $p_{\rm kin}$ 是数据中的运动压力。说明由预测场计算的升力是另一层工程输出。式（1）描述参考物理问题，网络按 §3.3 的数据目标训练。[P2](#p2)、[P5](#p5)、[P7](#p7)
3. **外推轴｜项目。** 定义 $Re\in[3,5]\times10^6$ 为训练区间。区间之外的雷诺数用于检验工况外推，攻角和翼型几何仍作为输入描述。这里解释外推含义，样本数量与协议在 §4.1 列出。[P1](#p1)、[P6](#p6)

### 2.2、冷却叶片与温度工况外推｜1.00 页

1. **工程物理问题｜外部文献＋项目。** 交代热气流、冷气和固体叶片构成共轭传热系统。说明固体导热与界面热流如何影响金属温度，附上参考 CFX 工程所采用的物性和边界说明。项目预测对象为固体节点温度 $T(\mathbf x)$，气侧条件通过工况输入和参考解体现。[R6](#r6)、[P3](#p3)、[P8](#p8)
2. **相似变量｜外部文献＋项目。** 先用冷却导向叶片的金属温度缩放理论和试验说明跨温度工况换算的物理背景，再引入本项目对固体域采用的温度变量。令 $T_g,T_c$ 分别为主流和冷气的进口总温，用式（2）给出正、逆变换。第 5 章的直接相似基线将低温参考场的 $\theta$ 代入新工况的逆变换。[R18](#r18)、[R19](#r19)、[P3](#p3)、[P8](#p8)

$$
\theta(\mathbf x)=\frac{T_g-T(\mathbf x)}{T_g-T_c},
\qquad T(\mathbf x)=T_g-(T_g-T_c)\,\theta(\mathbf x).
\tag{2}
$$

3. **外推条件｜项目。** 写明所有工况采用同一叶片和网格，节点之间具有一一对应关系，允许逐点拟合先验。交代两个测试进口温度 $1200$、$1616\,\mathrm K$ 和工况输入的五个参数：冷热流量比、温度比、压比、修正转速与修正流量。训练工况的完整数表只在 §5.1 出现。[P3](#p3)、[P8](#p8)

## 3、相似特化方法（Methodology）｜约 4 页

### 3.1、翼型流场的相似变换｜1.25 页

1. **正向变换｜项目。** 承接式（1），给出工况向量和网络学习的四个输出。用式（3）说明本文依据控制方程和任务设定选择相似变量，并在第 4 章比较区间外的预测误差。当前数据弦长为 $1\,\mathrm m$，$\nu=1.56\times10^{-5}\,\mathrm{m^2/s}$。按代码沿用数据自身的压力零点。[R16](#r16)、[R17](#r17)、[P2](#p2)、[P6](#p6)

$$
\begin{aligned}
\mathbf c&=(\lg Re,\sin\alpha,\cos\alpha),\\
\mathbf z&=\left(u/U_\infty,\ v/U_\infty,\
   2p_{\rm kin}/U_\infty^2,\ \lg(1+\nu_t/\nu)\right).
\end{aligned}
\tag{3}
$$

2. **近壁表示｜项目＋理论背景。** 说明同一个壁距在不同雷诺数下可能代表不同的流动尺度。写出两项查询特征 $\lg(1+d^*Re^{0.9})$ 与 $\lg(1+d^*Re^{0.2})$，其中 $d^*=d/L$ 在本数据上对应代码使用的壁距数值。指数和组合出自项目，边界层专著支持使用近壁尺度的物理动机。[P2](#p2)、[R5](#r5)
3. **逆变换与统计量｜项目。** 在训练集上将相似量按分量标准化。推理时先撤销标准化，再按下式恢复物理单位，供第 4 章计算压力分布和气动力。$\widehat z_c$ 表示已撤销标准化的网络输出。[P2](#p2)、[P6](#p6)

$$
(\widehat u,\widehat v,\widehat p_{\rm kin},\widehat\nu_t)
=\left(U_\infty\widehat z_1,\ U_\infty\widehat z_2,\
\tfrac12 U_\infty^2\widehat z_3,\ \nu(10^{\widehat z_4}-1)\right).
\tag{4}
$$

### 3.2、叶片温度先验与残差重构｜1.50 页

1. **先验拟合｜外部文献＋项目。** 冷却有效度研究表明，即使使用无量纲温度，温度比等工况变化仍可能引起偏移。以此说明为什么要在直接换算上增加修正。式（5）采用本项目的经验先验，以三个低温工况在同一节点的无量纲温度为样本，拟合其随 $g=T_g/(1000\,\mathrm K)$ 的一阶变化。设 $S$ 是实际参与拟合的工况集合，横线表示对 $S$ 取均值。第 5 章用逐级对照量化该先验的贡献。[R20](#r20)、[P3](#p3)、[P5](#p5)、[P8](#p8)

$$
\begin{aligned}
b_i(S)&=\frac{\sum_{j\in S}(g_j-\bar g_S)
                  (\theta_{ij}-\bar\theta_{i,S})}
                 {\sum_{j\in S}(g_j-\bar g_S)^2},\\
\theta_{{\rm lin},i}(g;S)&=\bar\theta_{i,S}+b_i(S)(g-\bar g_S).
\end{aligned}
\tag{5}
$$

2. **训练工况怎样留出｜项目。** 把先验来源写到公式里。令 $S_0$ 对应 $600/800/1000\,\mathrm K$ 三个先验算例，$j$ 是当前算例的身份标识。即使另一辅助算例也处于 $600\,\mathrm K$，其角色仍由算例身份决定。两个测试温度都使用完整 $S_0$。[P3](#p3)、[P5](#p5)

$$
S_j=\begin{cases}
S_0\setminus\{j\}, & j\in S_0,\\
S_0, & j\notin S_0 ,
\end{cases}
\qquad
r_{ij}=\theta_{ij}-\theta_{{\rm lin},i}(g_j;S_j).
\tag{6}
$$

3. **学习对象及其可检验后果｜项目＋代数推导。** 解释 $\theta_{\rm lin}$ 同时参与查询输入和输出重构。网络拟合 $r/\sigma_\theta$，其中 $\sigma_\theta$ 由训练集温度相似量估得，末层零初始化使初始预测等于先验。对同一给定测试工况，用式（2）可直接得到物理误差关系。后文由此把残差修正量和 K 单位的误差联系起来。[P3](#p3)

$$
\begin{aligned}
\widehat\theta_i&=\theta_{{\rm lin},i}+\widehat r_i,\\
\widehat T_i-T_i&=-(T_g-T_c)(\widehat r_i-r_i),\\
\mathrm{MAE}_T&=|T_g-T_c|\,
      \frac{1}{N_s}\sum_{i=1}^{N_s}|\widehat r_i-r_i|.
\end{aligned}
\tag{7}
$$

式（7）使用相同先验、已知的冷热进口温度和 $N_s$ 个等权固体节点，是变量变换的恒等式。跨工况比较时要使用各自的 $T_g-T_c$。

### 3.3、网格到场的映射与训练｜1.25 页

1. **共用架构｜项目＋来源。** 用图 1 讲清每个工况只编码一次。网格由 k-d 树分块，块内逐点映射后最大池化并叠加块中心位置编码。将空间块与工况 token 输入从 OmniArch 初始化的主干，查询点读取编码序列，分块恢复全场。指出翼型用 2048 个块，叶片用 4096 个块。继承的 8 个主干块和末端归一化与新建输入输出模块分别标出。注意力使用一句话说明查询对象及其来源即可。[P4](#p4)、[P6](#p6)、[P9](#p9)、[R10](#r10)、[R11](#r11)、[R14](#r14)

<p align="center"><strong>图 1　两类任务的数据流与可学习部分</strong><br>由项目 overview.svg 改绘。中间共用网格编码和查询解码，左支标翼型正逆变换，右支标叶片先验进入查询端并在输出端加回。用不同线型区分确定性物理变换和可训练映射。依据 P2–P4、P9。</p>

2. **训练目标｜项目。** 用一个目标覆盖两项任务。$y_{ic}$ 为训练目标，$w_i$ 为查询点权重，$a_c$ 为分量权重。翼型输出为标准化的四个相似量或有量纲对照量，叶片输出是缩放后的标量残差。说明本项目如何通过物理变量与先验利用方程知识，文献中的残差型 PINN 可作一句背景对照。[P2](#p2)、[P3](#p3)、[P5](#p5)、[R9](#r9)

$$
\mathcal L=
\frac{\sum_{i=1}^{N_q} w_i
  \left[C^{-1}\sum_{c=1}^{C}a_c(\widehat y_{ic}-y_{ic})^2\right]}
     {\sum_{i=1}^{N_q}w_i}.
\tag{8}
$$

3. **实现细节的去向｜项目。** 正文交代两组翼型配置的壁面/压力权重分别为 $(5,2)$ 与 $(1,1)$，因此第 4 章比较的是完整配置。叶片取 $C=1$、点和分量等权。AdamW、种子和推理聚合各用一句话说明，完整学习率、步数、设备和重写版本差异整理到附录，给物理研究问题留出正文篇幅。[P1](#p1)、[P5](#p5)、[P7](#p7)、[R12](#r12)

## 4、AirfRANS 雷诺数外推验证（Reynolds-number extrapolation on the AirfRANS benchmark）｜约 4 页

### 4.1、基准划分与比较设置｜0.75 页

1. **说明初稿的比较设置｜项目。** 项目复现记录给出 504 个训练算例和 496 个区间外测试算例。相似配置与有量纲配置在同一批 496 个算例上评价。训练范围及统计量来源见 §2.1、§3.1。[P1](#p1)、[P5](#p5)、[P6](#p6)、[R13](#r13)
2. **确定指标和统计单位｜项目＋文献。** 两套配置沿用同一气动力后处理。种子 0、1、2 分别按式（10）在 496 个测试算例上计算升力相对 $L_2$ 误差，然后汇报种子间的均值和标准差。表 1 同时报升力的 Spearman 秩相关。[P1](#p1)、[P7](#p7)、[R13](#r13)

**91% 对照的核查记录（供写作使用）**

| 查核来源 | 已核对的内容 |
|---|---|
| 项目 README 与复现记录 | GitHub 提交记录显示，“91%”与“454-case protocol”随摘要一起加入项目说明。该提交未列出模型名、论文表号、两侧误差或指标定义。复现记录给出了 496 例上的内部对照，代码将跨样本相对 $L_2$ 与逐例相对误差均值分别输出。基线出处尚待原始对照表确认。[项目摘要提交](https://github.com/Tarpelite/omniarch-aero/commit/b609fd2a7) · [P1](#p1) · [P7](#p7) |
| 数据集及公开划分 | AirfRANS 作者更新版附录 L 从预定义训练集合中留出约 10% 作验证。AIPhysics.org 明列雷诺数任务为 454 训练、50 验证、496 测试。这给出了“454”的一种可核对解释，项目采用的具体基线和划分仍需原始记录指认。[AirfRANS 附录 L](https://arxiv.org/html/2212.07564v3#A12) · [AIPhysics.org 数据划分](https://www.aiphysics.org/docs/training-data) |
| AirfRANS 原始模型 | 作者更新版附录 M 表 13 给出逐算例升力相对误差的均值。若原始对照采用该指标，需提取本项目同一划分下的逐算例相对误差均值；目前表 1 使用式（10）的跨算例相对 $L_2$。[AirfRANS 更新版 §4 及附录 M](https://arxiv.org/html/2212.07564v3) |
| Transolver 论文 | 项目评测代码提及 Transolver 的相对 $L_2$ 指标。其表 3 的 $C_L$ 误差 0.1030 对应表 7 所列的常规 800/200 任务。雷诺数外推的表 12 列为 500/500。表 6 把 0.2996 标成 $C_L$，附录表 13 的雷诺数列却标成 $C_D$。[P7](#p7) · [Transolver 作者稿表 3、6、7、12、13](https://arxiv.org/html/2402.02366v2) |
| Transolver 公开代码 | 训练入口读取官方任务划分，从 504 个雷诺数训练候选中按代码留出 50 个做验证，实际训练数为 454，测试仍走官方 496 例。这使 Transolver 成为有根据的候选基线。其公开评测代码对每个算例计算气动力系数的相对绝对误差再求均值，论文表注写的是相对 $L_2$。具体跑数版本与表中指标仍需原始评测输出确认。[训练划分代码](https://github.com/thuml/Transolver/blob/main/Airfoil-Design-AirfRANS/main.py#L27-L34) · [误差定义](https://github.com/thuml/Transolver/blob/main/Airfoil-Design-AirfRANS/utils/metrics.py#L46-L47) · [汇总代码](https://github.com/thuml/Transolver/blob/main/Airfoil-Design-AirfRANS/utils/metrics.py#L344-L365) |

**初稿取数。** 表 1、摘要和结论先用可追溯的 496 例配置对照，91% 暂保留在本核查记录。如果找到原始对照表，需核对基线模型与来源表号、两侧训练/验证/测试划分和算例 ID、气动力后处理、同一误差定义及对应数值，再按 $100(1-E_{\mathrm{ours}}/E_{\mathrm{baseline}})\%$ 核算降幅。

### 4.2、从流场到升力的误差｜2.00 页

1. **定义工程观测量｜项目·后处理的数学表达。** 对单位展向，令 $\mathbf n$ 指向从翼型表面进入流体的方向，$\mathbf s_w$ 是按此方向计算的单位密度黏性牵引，$\mathbf e_L=(-\sin\alpha,\cos\alpha)$。将壁面压力和剪切合力投影到升力方向。程序以面元长度和面值作离散求和，本数据弦长为 $L=1\,\mathrm m$。[P2](#p2)、[P7](#p7)、[R13](#r13)

$$
C_L=\frac{2}{U_\infty^2 L}
  \int_{\Gamma_w}
  \left(-p_{\rm kin}\mathbf n+\mathbf s_w\right)\cdot\mathbf e_L
  \,\mathrm d\ell .
\tag{9}
$$

2. **解释场误差为什么会影响升力｜由式（9）直接得到。** 对同一几何和工况，两次积分相减，令 $\delta$ 表示预测值减参考值。压力偏差可能在上下表面抵消，也可能累积，因此同时看压力曲线和积分量。比较沿用正式后处理，包含壁面剪切，评测时对壁面预测速度和湍流黏度按官方流程置零。[P2](#p2)、[P7](#p7)

$$
\delta C_L=
\frac{2}{U_\infty^2 L}\int_{\Gamma_w}
   (-\delta p_{\rm kin}\mathbf n+\delta\mathbf s_w)
      \cdot\mathbf e_L\,\mathrm d\ell ,
\qquad
\varepsilon_{C_L}
=\frac{\|\widehat{\mathbf C}_L-\mathbf C_L\|_2}{\|\mathbf C_L\|_2}.
\tag{10}
$$

粗体 $\mathbf C_L$ 收集测试集中每个算例的升力系数。第二个式子先跨算例取范数，与逐例求百分比后平均有不同含义。

3. **给出主要性能结果｜项目。** 496 例上的升力相对 $L_2$ 误差由有量纲配置的 $0.0514\pm0.0038$ 降到相似配置的 $0.0182\pm0.0026$，按种子均值计算降幅约为 65%。相似配置的升力排序相关系数为 $0.9996$。写明一个指标衡量幅值误差，一个衡量设计排序。[P1](#p1)、[P7](#p7)

<p align="center"><strong>表 1　496 个雷诺数外推算例上的流场与气动力精度</strong><br>两行分别列出有量纲配置和相似配置，主列为种子数、升力相对 L₂ 误差及升力秩相关。表注标明训练/测试样本数、误差定义与种子汇总方式，阻力和场误差可按评测输出补列。依据 P1、P7。</p>

4. **用空间结果解释表 1｜项目＋图表制作。** 从训练区间两侧各选一个代表工况，记录选择规则。沿上下表面分别观察压力偏差出现的位置，回到式（9）解释其对升力的可能影响；剪切与压力的定量分解按同一后处理输出填写。[P2](#p2)、[P7](#p7)

<p align="center"><strong>图 2　低、高雷诺数外推下的压力场与升力来源</strong><br>两行分别为低于训练下界和高于上界的工况。每行并列参考压力、预测压力和误差场，附上下表面压力系数曲线。图注列算例、雷诺数、攻角及升力误差。调用对应预测场和表面坐标制作。依据 P2、P7。</p>

### 4.3、外推性能分析与推理耗时｜1.25 页

1. **解释两组配置比较到了什么｜项目。** 在表 1 的结果后一起交代查询表示、输入维度和损失权重差别。直接称为“相似特化配置相对于有量纲配置的改善”。重写实现载入原权重后复现相应种子结果，可将逐种子明细列入补充材料。[P1](#p1)、[P2](#p2)、[P5](#p5)
2. **解释编码信息的作用｜项目。** 项目记录在置换为另一翼型的块 token 后，输出变化约 0.24，对应归一化输出尺度约 0.72。用这项干预说明模型对几何信息敏感，并引出 §5.3 的固定网格对照。[P1](#p1)、[P4](#p4)
3. **报告计算代价｜项目。** 单工况流场预测约 $0.22\,\mathrm s$，RANS 计算约 $25\,\mathrm{min}$。紧随数字标明设备、算例规模、单模型或集成、计时边界。当前推理脚本在 GPU 同步后对一次工况预测计时，写盘位于计时段之后。用一个短段或表 1 表注交代，避免另起“效率”章。[P1](#p1)、[P7](#p7)

## 5、冷却涡轮叶片温度外推与讨论（Temperature extrapolation for a cooled turbine blade）｜约 4 页

### 5.1、工程算例与对照方法｜1.00 页

1. **明确工程对象和参考解｜项目＋文献。** 一种冷却转子叶片、同一网格、七个收敛 CFX 工况，任务针对 3,304,055 个固体节点。说明参考场来源、气侧表面定义及数据提取一致性。冷却设计背景引用传热专著，几何、边界和材料信息取自工程设置。[P3](#p3)、[P8](#p8)、[R6](#r6)
2. **把训练集与先验集分清｜项目。** 五个训练算例中有三个用于建立先验。两个高温测试工况均使用这三个先验算例。直接相似换算沿用最近的先验工况，即 $1000\,\mathrm K$ 的 $\theta$ 场；线性先验按式（5）计算；完整模型再加学习残差。三种方法在同一网格上比较。[P1](#p1)、[P3](#p3)、[P8](#p8)

<p align="center"><strong>表 2　七个叶片工况及其在预测流程中的角色</strong><br>按数据说明逐行列主流与冷气进口总温、工况标识和“训练／拟合先验／测试”三列。两个主流温度同为 600 K 的算例保留各自的冷气温度。五个工况相似参数的详细数值可随补充材料给出。依据 P3、P5、P8。</p>

### 5.2、金属温度场与热点误差｜1.75 页

1. **交代汇总方式｜项目。** 五个种子的温度预测先按节点平均，再以 CFX 为参照计算整片金属温度 MAE。算例是工况，固体节点是同一算例的空间样本。下式固定了集成、取绝对值和空间平均的先后顺序，$M=5$。[P1](#p1)、[P3](#p3)、[P7](#p7)

$$
\widehat T_i^{\,\rm ens}=\frac1M\sum_{m=1}^{M}\widehat T_i^{(m)},
\qquad
\mathrm{MAE}_{T}^{\,\rm ens}
=\frac1{N_s}\sum_{i=1}^{N_s}\bigl|\widehat T_i^{\,\rm ens}-T_i\bigr| .
\tag{11}
$$

2. **先比较整体温度｜项目。** 在 $1200\,\mathrm K$，三种方法的 MAE 依次为 $5.32$、$1.84$、$1.56\,\mathrm K$；在 $1616\,\mathrm K$，分别为 $20.96$、$5.34$、$4.90\,\mathrm K$。按式（7）解释绝对误差的工况尺度。例如 $1616\,\mathrm K$ 工况的 $T_c=901\,\mathrm K$，$4.90\,\mathrm K$ 对应约 $4.90/715=0.00685$ 的无量纲温度 MAE。这是同一结果的单位变换。[P1](#p1)、[P3](#p3)、[P8](#p8)

<p align="center"><strong>表 3　相似换算、温度先验和残差模型的两工况比较</strong><br>行按三种方法排，列按 1200 K 和 1616 K 分组。主列用全体固体节点等权 MAE（K），表注说明基线与五模型平均场的差异。表面 MAE、最高温度偏差和热点位移取自同口径的评价输出。依据 P1、P3、P7。</p>

3. **从平均误差转到工程量｜项目。** 区分最高温度偏差 $\max_i\widehat T_i-\max_i T_i$、在真实热点位置评价的温度偏差，以及预测热点和真实热点之间的距离。只有实际局部场能回答“高温区域在哪里、偏差多大”。[P3](#p3)、[P7](#p7)、[P8](#p8)

<p align="center"><strong>图 3　两个高温工况的金属温度、误差和热点位置</strong><br>以叶片几何小图标出气侧表面和比较截面。两工况分行，绘 CFX 温度、集成预测和绝对误差，标真实与预测热点，用同视角与可比较的色标。数据取自固体温度场、节点坐标和表面索引。依据 P3、P7、P8。</p>

### 5.3、先验贡献与适用范围｜1.25 页

1. **逐步解释改善｜项目＋计算。** 在 $1616\,\mathrm K$，用线性先验代替直接换算减少约 $15.62\,\mathrm K$ 的 MAE，学习修正再减少约 $0.44\,\mathrm K$。$1200\,\mathrm K$ 时两步分别为约 $3.48$ 和 $0.28\,\mathrm K$。这些是表 3 相邻方法的差值，区分了两种工程收益。[P1](#p1)、[P3](#p3)
2. **回答“这一步改善来自哪里”｜项目。** 在叶片原检查点上，将块 token 换成噪声、置零或将工况参数减半，输出变化小于 $10^{-8}$，输出尺度约为 $10^{-3}$。固定网格使不同工况的空间块信息相同，查询点的温度先验本身已编码工况差别。与 §4.3 对照，由此将叶片网络的增益解释为这套几何上的逐点先验修正。[P1](#p1)、[P3](#p3)、[P4](#p4)

<p align="center"><strong>图 4　翼型与叶片分别使用了哪一路信息</strong><br>用两个示意面板标出干预点和预测响应。翼型标明跨翼型替换块 token 的响应及其输出尺度，叶片标明三类扰动、统一响应上界及先验直达查询端的位置。保留各自归一化口径，避免跨任务共用一个绝对值纵轴。可由 VERIFY 中的记录制作。依据 P1、P3、P4。</p>

3. **工程讨论｜项目＋外部文献。** 以表 3 比较直接换算、逐节点先验和残差网络的误差，再联系文献中温度比、绝对温度及气体物性对冷却有效度的影响。文献提供解释温度偏移的物理背景，本文用固定转子叶片的 CFX 结果检验先验与残差修正的效果。逐节点先验依赖节点对应，跨叶型预测需重新建立映射或先验。[P1](#p1)、[P8](#p8)、[R6](#r6)、[R18](#r18)、[R19](#r19)、[R20](#r20)

## 6、结论（Conclusion）｜约 1 页

1. **一句主结论、两个适用条件｜项目。** 总结在非结构网格上引入任务相关相似表示的方法。翼型的工况变量是雷诺数，叶片的工况变量是进口温度。说明跨任务共用的是计算思路，两套模型分别完成训练。[P1](#p1)、[P4](#p4)
2. **各用一个结果回答引言里的问题｜项目。** 翼型报告 496 例上两套项目配置的升力相对 $L_2$。叶片报告 1616 K 工况下相似换算、先验和五种子集成修正的金属温度 MAE。在指标旁写明各自的对照设置。[P1](#p1)、[P7](#p7)
3. **给出能用于后续设计的认识｜项目＋写作建议。** 相似变换决定网络还需学习什么；几何变化和查询端可用信息又决定编码主干在该任务中起什么作用。以固定叶片逐点先验的可迁移范围收尾，用一句话指出跨几何检验将回答什么问题。[P1](#p1)、[P3](#p3)

## 从框架到投稿稿件

**六章的论证顺序可用于写作，当前稿件仍属于规划稿。** 定稿时，先在 §3 写清相似变换和先验的构造，再用 §4、§5 的结果检验其工程作用。正文优先保留上述 4 图、3 表，原计划中单独的配置表、分布图、计时表和逐种子图，分别并入图注、结果表或补充材料。篇幅预算含图表和公式，也允许成稿时在同章内调配。

第 5 节为冷却涡轮叶片算例。提交版还需处理预留图表、移除内部规划行，并完成作者信息和声明。指南要求摘要不超过 250 个英文词、关键词 1–7 个，并要求章节清楚编号。17 页、11 个小节和上述数学表达均为针对本稿的写作安排。[CMAME 作者指南](https://www.sciencedirect.com/journal/computer-methods-in-applied-mechanics-and-engineering/publish/guide-for-authors)

## 项目来源索引

以下链接以论文文件夹中的 omniarch-aero-main/ 为根目录。以下区分具体实现和项目结果，写作时可按标记回到原文件。

<a id="p1"></a>
**P1｜项目说明与结果记录**  
[README.md](./omniarch-aero-main/README.md)、
[README_zh.md](./omniarch-aero-main/README_zh.md)、
[VERIFY.md](./omniarch-aero-main/VERIFY.md)。用于核心结果、随机种子、原实验与重写实现的关系、编码信息依赖性等。

<a id="p2"></a>
**P2｜翼型任务实现**  
[tasks/airfrans.py](./omniarch-aero-main/tasks/airfrans.py)。重点为 query_features、targets、to_physical、param_values、get_batch 及正式气动力计算。

<a id="p3"></a>
**P3｜叶片任务实现**  
[tasks/blade.py](./omniarch-aero-main/tasks/blade.py)。重点为 theta_of、T_of、theta_prior、训练时的先验留出、残差预测及 temperature_metrics。

<a id="p4"></a>
**P4｜网络实现**  
[model.py](./omniarch-aero-main/model.py)、
[tasks/__init__.py](./omniarch-aero-main/tasks/__init__.py)。重点为 kd_blocks、AeroNet.encode/decode、CrossBlock、load_omniarch。

<a id="p5"></a>
**P5｜训练与配置**  
[train.py](./omniarch-aero-main/train.py)、
[config/airfrans.py](./omniarch-aero-main/config/airfrans.py)、
[config/airfrans_raw.py](./omniarch-aero-main/config/airfrans_raw.py)、
[config/blade.py](./omniarch-aero-main/config/blade.py)。用于损失函数、优化、预算及两类任务的设置差异。

<a id="p6"></a>
**P6｜数据准备**  
[data/airfrans/prepare.py](./omniarch-aero-main/data/airfrans/prepare.py)、
[data/blade/prepare.py](./omniarch-aero-main/data/blade/prepare.py)。用于数据划分、统计标准化、几何特征和空间块采样。

<a id="p7"></a>
**P7｜预测与评价**  
[predict.py](./omniarch-aero-main/predict.py)、
[evaluate.py](./omniarch-aero-main/evaluate.py)，以及 P2、P3 中的评价函数。用于物理量恢复、单种子与集成、误差和计时口径。

<a id="p8"></a>
**P8｜叶片数据说明**  
[data/blade/README.md](./omniarch-aero-main/data/blade/README.md)。用于七个工况的温度、训练/先验/测试角色、网格规模、表面区域和数据提取记录。

<a id="p9"></a>
**P9｜图示、运行入口和环境**  
[assets/overview.svg](./omniarch-aero-main/assets/overview.svg) 为现有框架图；scripts/ 中的脚本、configurator.py 和 requirements.txt 提供运行与环境信息。.gitignore 说明权重、原始数据和运行输出在代码目录中的管理方式。

## 外部参考文献及其在本文中的作用

**正文编号。** R1–R20 是本框架的查阅顺序。中英文稿引用同一组文献，PDF 中的编号由正文首次引用顺序生成。参数化降阶和 PINN 文献分别用于交代多工况代理建模背景和物理信息进入损失函数的已有途径。

**初稿共 20 篇。** R1–R12 以经典理论、专著和代表性方法为主。R13–R15 是数据集、预训练模型和直接相关方法的出处。本轮增加两篇基于 Buckingham $\Pi$ 定理的学习研究和三篇冷却叶片温度缩放研究，分别用于交代方法先例、物理依据和工程讨论。

**计数说明**：下列数字为 2026-11-21 查询得到的 Crossref 或 Semantic Scholar 条目计数，两者覆盖范围不同，也未排除自引，不作为统一排名。会议年份采用正式会议记录，预印本条目的年份或旧题名差异另作说明。书籍核对了版次、书目信息和相关主题，具体工程关联式在使用时应落实到相应章节。

<a id="r1"></a>
### R1｜流体机器学习背景

Brunton, S. L., Noack, B. R., and Koumoutsakos, P. **Machine Learning for Fluid Mechanics**. Annual Review of Fluid Mechanics, 52, 477–508, 2020. DOI: 10.1146/annurev-fluid-010719-060214。**高引用领域综述，Crossref 3,045 次**。用于引言中的需求、数据驱动方法和适用边界，不用于证明本项目的误差或时间。[原文入口](https://doi.org/10.1146/annurev-fluid-010719-060214) · [作者公开全文](https://faculty.washington.edu/sbrunton/ARFM2020.pdf) · [计数来源](https://api.crossref.org/works/10.1146/annurev-fluid-010719-060214)

<a id="r2"></a>
### R2｜参数化问题与重复求解

Benner, P., Gugercin, S., and Willcox, K. **A Survey of Projection-Based Model Reduction Methods for Parametric Dynamical Systems**. SIAM Review, 57(4), 483–531, 2015. DOI: 10.1137/130932715。**高引用降阶综述，Crossref 1,814 次**。用于解释多参数重复求解和低成本代理的需求，引用时保留其投影降阶方法的研究范围。[原文入口](https://doi.org/10.1137/130932715) · [作者公开全文](https://kiwi.oden.utexas.edu/papers/Parametric-model-reduction-survey-Benner-Gugercin-Willcox.pdf) · [计数来源](https://api.crossref.org/works/10.1137/130932715)

<a id="r3"></a>
### R3｜量纲分析与相似理论

Buckingham, E. **On Physically Similar Systems; Illustrations of the Use of Dimensional Equations**. Physical Review, 4(4), 345–376, 1914. DOI: 10.1103/PhysRev.4.345。**经典原始理论，Crossref 3,044 次**。用于无量纲参数和物理相似的基础论述；本项目的网络收益和具体指数由项目设计与实验说明。[出版社原文](https://journals.aps.org/pr/abstract/10.1103/PhysRev.4.345) · [计数来源](https://api.crossref.org/works/10.1103/PhysRev.4.345)

<a id="r4"></a>
### R4｜湍流与 RANS 背景

Pope, S. B. **Turbulent Flows**. Cambridge University Press, 2000. DOI: 10.1017/CBO9780511840531。**经典专著，Crossref 7,736 次**。用于平均流、湍流统计与闭合背景；AirfRANS 和叶片的具体求解设置仍分别引用其数据及项目来源。[出版社入口](https://doi.org/10.1017/CBO9780511840531) · [计数来源](https://api.crossref.org/works/10.1017/CBO9780511840531)

<a id="r5"></a>
### R5｜边界层与近壁尺度

Schlichting, H., and Gersten, K. **Boundary-Layer Theory**, 9th edition. Springer, 2017. DOI: 10.1007/978-3-662-52919-5。**经典专著，Crossref 1,207 次**。用于解释近壁结构与尺度变量背景；本框架没有将项目采用的 $Re^{0.9}$、$Re^{0.2}$ 特征组合归作该书直接给出的算法。[出版社与目录](https://link.springer.com/book/10.1007/978-3-662-52919-5) · [计数来源](https://api.crossref.org/works/10.1007/978-3-662-52919-5)

<a id="r6"></a>
### R6｜涡轮传热与冷却

Han, J.-C., Dutta, S., and Ekkad, S. **Gas Turbine Heat Transfer and Cooling Technology**, 2nd edition. CRC Press, 2013. DOI: 10.1201/b13616。**领域经典专著，Crossref 419 次**。用于冷却叶片的传热背景、工况与局部热量评价；逐节点线性温度先验的实现来源是 P3。年份按出版社版权年 2013 标注，Crossref 登记的出版日期为 2012。[出版社版本信息](https://www.routledge.com/Gas-Turbine-Heat-Transfer-and-Cooling-Technology-2nd-Edition/Han-Dutta-Ekkad/p/book/9780429107115) · [DOI](https://doi.org/10.1201/b13616) · [计数来源](https://api.crossref.org/works/10.1201/b13616)

<a id="r7"></a>
### R7｜Fourier neural operator

Li, Z., Kovachki, N., Azizzadenesheli, K., et al. **Fourier Neural Operator for Parametric Partial Differential Equations**. 第 9 届国际学习表征会议（ICLR 2021）。**神经算子代表性原始论文**，引用正式会议版。用于引言中的函数空间映射与神经算子背景。[ICLR 2021 论文目录](https://iclr.cc/Downloads/2021) · [正式会议论文 PDF](https://openreview.net/pdf?id=c8P9NQVtmnO)

<a id="r8"></a>
### R8｜DeepONet 与算子学习

Lu, L., Jin, P., Pang, G., Zhang, Z., and Karniadakis, G. E. **Learning nonlinear operators via DeepONet based on the universal approximation theorem of operators**. Nature Machine Intelligence, 3, 218–229, 2021. DOI: 10.1038/s42256-021-00302-5。**神经算子代表性原始论文，Crossref 3,753 次**。用于算子学习与坐标查询的相关工作；本项目的交叉注意力实现由 P4 说明，不称为 DeepONet 原结构。[正式论文](https://doi.org/10.1038/s42256-021-00302-5) · [相关预印本](https://arxiv.org/abs/1910.03193) · [计数来源](https://api.crossref.org/works/10.1038/s42256-021-00302-5)

<a id="r9"></a>
### R9｜物理信息进入学习过程的另一条路线

Raissi, M., Perdikaris, P., and Karniadakis, G. E. **Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations**. Journal of Computational Physics, 378, 686–707, 2019. DOI: 10.1016/j.jcp.2018.10.045。**高引用原始方法论文，Crossref 21,302 次**。用于说明物理方程约束与本文相似表示、先验设计之间的联系及区别；本文当前损失函数按 P5 描述。[正式论文](https://doi.org/10.1016/j.jcp.2018.10.045) · [作者早期方法说明](https://arxiv.org/abs/1711.10561) · [计数来源](https://api.crossref.org/works/10.1016/j.jcp.2018.10.045)

<a id="r10"></a>
### R10｜点集特征与对称池化

Qi, C. R., Su, H., Mo, K., and Guibas, L. J. **PointNet: Deep Learning on Point Sets for 3D Classification and Segmentation**. CVPR, 2017. DOI: 10.1109/CVPR.2017.16。**高引用点集方法论文，Crossref 4,065 次**。用于逐点网络与对称聚合思想；项目的 k-d 块划分和与主干的连接属于 P4、P6 所记录的具体实现。作者顺序按论文原文核对。[作者预印本](https://arxiv.org/abs/1612.00593) · [DOI](https://doi.org/10.1109/CVPR.2017.16) · [计数来源](https://api.crossref.org/works/10.1109/CVPR.2017.16)

<a id="r11"></a>
### R11｜注意力机制

Vaswani, A., Shazeer, N., Parmar, N., et al. **Attention Is All You Need**. Advances in Neural Information Processing Systems, 30, 2017。**经典原始方法，Semantic Scholar 204,117 次**。仅用于第 3.3 节的注意力与编码—解码背景；引用时不把该文的机器翻译实验当作 PDE 结果。[会议原文](https://proceedings.neurips.cc/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html) · [计数条目](https://www.semanticscholar.org/paper/204e3073870fae3d05bcbc2f6a8e263d9b72e776)

<a id="r12"></a>
### R12｜AdamW

Loshchilov, I., and Hutter, F. **Decoupled Weight Decay Regularization**. 第 7 届国际学习表征会议（ICLR 2019）。**AdamW 的原始论文**，引用正式会议版。用于说明 AdamW 的来源，具体学习率和衰减设置见项目配置。[ICLR 2019 论文目录](https://iclr.cc/Downloads/2019) · [正式会议论文 PDF](https://openreview.net/pdf?id=Bkg6RiCqY7)

<a id="r13"></a>
### R13｜本项目所用公开数据集

Bonnet, F., Mazari, J., Cinnella, P., and Gallinari, P. **AirfRANS: High Fidelity Computational Fluid Dynamics Dataset for Approximating Reynolds-Averaged Navier–Stokes Solutions**. NeurIPS Datasets and Benchmarks Track, 2022. DOI 10.52202/068431-1705。**数据集原始引用**，Semantic Scholar 预印本条目计数 155。数据集引用使用会议原文。核查论文基线数值时采用作者勘误后的 arXiv v3，训练和测试设置见附录 L，主要基线结果见附录 M。本文自己的数据划分见 P6。[会议原文](https://proceedings.neurips.cc/paper_files/paper/2022/hash/94ab7b23a345f93333eac8748a66c763-Abstract-Datasets_and_Benchmarks.html) · [作者勘误说明](https://github.com/Extrality/AirfRANS#airfrans) · [修正版全文](https://arxiv.org/html/2212.07564v3) · [计数条目](https://www.semanticscholar.org/paper/e8ca130df3f62798fbf432982e67aa93a5561a76)

<a id="r14"></a>
### R14｜本项目预训练主干的来源

Chen, T., Zhou, H., Li, Y., et al. **OmniArch: Building Foundation Model for Scientific Computing**. Proceedings of the 42nd International Conference on Machine Learning, PMLR 267, 9860–9887, 2025。**必要的模型原始引用**，Semantic Scholar 关联条目计数 12，条目年份为预印本年份 2024。用于模型来源和预训练背景，当前项目具体迁移内容引用 P4。[正式会议论文](https://proceedings.mlr.press/v267/chen25cp.html) · [计数条目](https://www.semanticscholar.org/paper/b66093009fdec197e1ad5cb7e71eee1ffcc976dd)

<a id="r15"></a>
### R15｜复杂几何 PDE 与翼型相关方法

Wu, H., Luo, H., Wang, H., Wang, J., and Long, M. **Transolver: A Fast Transformer Solver for PDEs on General Geometries**. Proceedings of the 41st International Conference on Machine Learning, PMLR 235, 53681–53705, 2024。用于复杂几何的算子学习和翼型评价相关工作。常规任务采用表 7 的 800/200，雷诺数外推参见表 6 与附录 E.3，出处核查见 §4.1。[正式会议论文](https://proceedings.mlr.press/v235/wu24r.html) · [作者全文](https://arxiv.org/html/2402.02366v2)

<a id="r16"></a>
### R16｜从数据识别无量纲群

Bakarji, J., Callaham, J., Brunton, S. L., and Kutz, J. N. **Dimensionally consistent learning with Buckingham Pi**. Nature Computational Science, 2(12), 834–844, 2022. DOI 10.1038/s43588-022-00355-5。用于 §1、§3.1，交代从数据识别无量纲群的代表性工作。本文按控制方程与任务设置预先定义相似变量，学习目标是网格上的物理场。[出版社原文](https://www.nature.com/articles/s43588-022-00355-5) · [作者预印本](https://arxiv.org/abs/2202.04643)

<a id="r17"></a>
### R17｜基于无量纲变量的跨尺度学习

Oppenheimer, M. W., Doman, D. B., and Merrick, J. D. **Multi-scale physics-informed machine learning using the Buckingham Pi theorem**. Journal of Computational Physics, 474, 111810, 2023. DOI 10.1016/j.jcp.2022.111810。用于 §1、§3.1，说明无量纲变量用于跨尺度建模及外推已有直接先例。本文将贡献落到非结构网格全场预测、OmniArch 的任务适配和固定叶片的温度残差建模。外推精度由各算例的区间外测试给出。[出版社原文](https://www.sciencedirect.com/science/article/pii/S0021999122008737)

<a id="r18"></a>
### R18｜冷却金属温度缩放的理论

Luque, S., Jones, T. V., and Povey, T. **Theory for the scaling of metal temperatures in cooled compressible flows**. International Journal of Heat and Mass Transfer, 102, 331–340, 2016. DOI 10.1016/j.ijheatmasstransfer.2016.06.025。用于 §2.2、§5.3，说明在可压缩共轭传热中，金属温度缩放与温度尺度的选择及对流、导热条件有关。该文推导了自己的温度参数。本文式（2）的温度定义和式（5）的经验先验按项目实现写。[出版社原文](https://doi.org/10.1016/j.ijheatmasstransfer.2016.06.025)

<a id="r19"></a>
### R19｜冷却导向叶片温度缩放的实验

Luque, S., Jones, T. V., and Povey, T. **Scaling of Turbine Metal Temperatures in Cooled Compressible Flows—Experimental Demonstration of a New Theory**. Journal of Turbomachinery, 139(8), 081001, 2017. DOI 10.1115/1.4035831。用于 §2.2、§5.3，给出高压涡轮导向叶片在匹配气动条件下，将低温台架壁温推算到发动机工况的实验先例。本文转子叶片的全固体域误差由自己的 CFX 工况评价。[出版社原文](https://doi.org/10.1115/1.4035831) · [牛津大学作者存档](https://ora.ox.ac.uk/objects/uuid:beca5469-0362-4b48-8456-2862bd091380)

<a id="r20"></a>
### R20｜温度比对整体冷却有效度的影响

Cartlidge, J., and Povey, T. **Fundamentals of Scaling of Overall Cooling Effectiveness With Temperature Ratio**. Journal of Turbomachinery, 146(1), 011008, 2024（2023 年在线发表）. DOI 10.1115/1.4063730。用于 §1、§3.2、§5.3，说明整体冷却有效度还可能随温度比、绝对温度及主流气体性质变化。用其结果解释引入工况修正的动机，逐节点线性先验的效果以本文表 3 检验。[出版社原文](https://doi.org/10.1115/1.4063730) · [牛津大学全文](https://ora.ox.ac.uk/objects/uuid%3Ac9880e06-1616-4f81-a306-a8f0d0be2732/files/sbv73c2154)
