# Python
## rainfall_forecast_verification.py
主要功能概述
这个程序用于对比ECMWF模式的48小时提前预报与站点观测数据，评估模式对暴雨（50mm阈值）的预报能力。
核心模块解析
1. 数据读取模块
•	read_station_rainfall(date_str) - 读取站点降水观测数据
o	从固定路径读取格式为YYYYMMDD的站点降水文件
o	处理缺测值（9999.0）
o	返回包含站点ID、经纬度和降水量的列表
•	read_ec_rainfall(rain_date_str) - 读取ECMWF模式预报数据
o	自动计算起报时间（提前48小时）
o	从NetCDF文件中读取总降水量
o	计算24小时累积降水（tppm48 - tppm24）
o	单位转换（米→毫米）
o	截取研究区域（20-25.5°N，109.5-117.5°E）
2. 检验评估模块
•	calculate_confusion_matrix() - 计算混淆矩阵
o	根据50mm暴雨阈值分类：
	H（命中）: 观测和预报均超过50mm
	F（空报）: 预报超过但观测未超过
	M（漏报）: 观测超过但预报未超过
	N（正确否定）: 两者均未超过
3. 数据处理模块
•	interpolate_data_to_stations() - 调用data_interpolation模块将模式格点数据插值到站点位置
•	process_single_date() - 处理单个日期的完整流程
•	main() - 主函数，批量处理所有日期
数据流程
Plain Text
日期文件 → 逐个日期处理 → 
  ├─ 读取站点观测
  ├─ 读取EC模式48h预报
  ├─ 模式数据插值到站点
  ├─ 计算混淆矩阵
  └─ 保存结果
输出结果
程序会生成两个文件：
1.	摘要文件 - 每个日期的H/F/M/N统计
2.	详细文件 - 每个站点的详细状态（包括观测值、预报值和状态码）
应用场景
这个程序适用于气象领域的数值预报检验，特别是针对华南前汛期暖区暴雨的预报效果评估，帮助气象工作者了解ECMWF模式的预报性能。
 
## grib2_to_nc.py
### 功能描述
该脚本用于将 GRIB2 格式 的气象数据文件转换为 NetCDF 格式 （.nc 文件）。GRIB2 和 NetCDF 都是气象领域常用的数据格式，NetCDF 更易于用 xarray、pandas 等工具处理。

主要特性：

- 自动检测 GRIB2 文件中的层级类型（surface、isobaricInhPa、heightAboveGround 等）
- 当文件中包含多种层级类型时，自动拆分并分别转换
- 支持常见的气象层级类型（地面、等压面、土壤层等）
### 使用方法
命令行格式：

```
python grib2_to_nc.py <输入文件.grib2>
```
示例：

```
python grib2_to_nc.py data.grib2
```
### 输出
- 单一层级类型：输出 <输入文件名>.nc
- 多层级类型：输出多个文件，如 data_surface.nc 、 data_isobaricInhPa.nc 等
### 依赖
- xarray
- cfgrib 引擎


## grib_to_nc.py
### 功能描述
该脚本用于将 GRIB/GRIB2 格式 的气象数据文件转换为 NetCDF 格式 （.nc 文件）。

主要特性：

- 支持 .grib 和 .grib2 两种格式自动识别
- 自动检测并处理 GRIB 文件中的多种层级类型（地面、等压面、土壤层等）
- 当文件中包含多种层级类型时，自动拆分并分别转换
### 使用方法
命令行格式：

```
python grib_to_nc.py <输入文件.grib 或 .grib2>
```
示例：

```
# GRIB1 文件
python grib_to_nc.py data.grib

# GRIB2 文件
python grib_to_nc.py data.grib2
```
### 输出
- 单一层级类型：输出 <输入文件名>.nc
- 多层级类型：输出多个文件，如 data_surface.nc 、 data_isobaricInhPa.nc 等
### 依赖
- xarray
- cfgrib 引擎
### 注意事项
- 原文件不会被删除或修改
- 如果输出文件已存在，会直接覆盖


## data_interpolation.py
### 功能描述
该脚本提供气象数据的 空间插值功能 ，将网格化的气象数据（如EC模式的格点数据）插值到指定站点的位置。

主要特性：

- 自动识别经纬度维度（支持 lon / lat 、 longitude / latitude 、 x / y 等命名方式）
- 支持线性插值方法
- 自动处理经纬度排序问题
- 边界外的站点返回 NaN 值
- 自动处理多维数据（如包含气压层维度的数据）
### 核心函数
interpolate_data_to_stations(station_data, data, variable_name)

参数 类型 说明 station_data list 站点数据列表，每个站点需包含 longitude 和 latitude 字段 data xarray.DataArray 网格化的气象数据 variable_name str 变量名，用于在结果中存储插值结果

### 使用示例
```
from data_interpolation import 
interpolate_data_to_stations

# 站点数据格式
station_data = [
    {'station_id': '57988', 
    'longitude': 113.345, 
    'latitude': 25.110},
    {'station_id': '57989', 
    'longitude': 113.763, 
    'latitude': 25.059},
]

# 假设 rhum_data 是 xarray.DataArray
interpolated = 
interpolate_data_to_stations
(station_data, rhum_data, 'rhum')
```
### 依赖
- numpy
- scipy （ scipy.interpolate.RegularGridInterpolator ）
