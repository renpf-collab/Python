import os
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from data_interpolation import interpolate_data_to_stations

# 读取站点降水数据
def read_station_rainfall(date_str):
    # 构建文件路径
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:8]
    file_path = fr'/mnt/f/data/StationRain/{year}/{year}{month}{day}/{year}{month}{day}20.txt'
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 站点降水文件不存在: {file_path}")
        return None
    else:
        # 存储数据的列表
        stations = []
        
        # 读取文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 去除行尾的换行符并分割数据
                    parts = line.strip().split()
                    if len(parts) == 4:
                        # 提取数据
                        station_id = parts[0]
                        longitude = float(parts[1])
                        latitude = float(parts[2])
                        rainfall = float(parts[3])
                        
                        # 处理缺测值（9999.0）
                        if rainfall != 9999.0:
                            # 添加到列表
                            stations.append({
                                'station_id': station_id,
                                'longitude': longitude,
                                'latitude': latitude,
                                'rainfall': rainfall
                            })
            
            print(f"✅ 成功读取 {len(stations)} 个站点的降水数据")
            return stations
            
        except Exception as e:
            print(f"❌ 读取站点降水文件时出错: {e}")
            return None

# 读取EC模式降水数据（提前48小时预报）
def read_ec_rainfall(rain_date_str):
    # 计算起报日期和时间（提前2天，12时起报，世界时）
    # 假设rain_date_str是YYYYMMDD格式，对应实况降水时间为当天北京时20时
    # 转换为世界时（UTC）
    rain_date = datetime.strptime(rain_date_str + "20", "%Y%m%d%H")
    rain_date_utc = rain_date - timedelta(hours=8)  # 转换为世界时
    # 起报时间：提前48小时，即2天前的世界时12时
    init_date_utc = rain_date_utc - timedelta(days=2)
    init_date_utc = init_date_utc.replace(hour=12, minute=0, second=0, microsecond=0)
    IniFyear = init_date_utc.year
    IniFmonth = init_date_utc.month
    Inidate = init_date_utc.strftime("%Y%m%d")
    Ihh = "12"  # 12时起报（世界时）
    
    # 定义经纬度范围
    lats = 20.0
    latn = 25.5
    lons = 109.5
    lonn = 117.5
    
    # 构建EC模式数据文件路径
    url_tp = f"/mnt/f/data/Model/ECMWF/{IniFyear}{IniFmonth:02d}_tppm.nc"
    
    # 读取EC模式数据
    try:
        fecmwfthintp = xr.open_dataset(url_tp)
        
        # 处理时间 - 直接使用datetime对象来比较，避免时区问题
        time = fecmwfthintp['time']
        time_values = time.values
        
        # 构建目标时间对象
        target_date_str = f"{Inidate} {Ihh}:00:00"
        target_datetime = datetime.strptime(target_date_str, "%Y%m%d %H:%M:%S")
        
        # 打印调试信息
        print(f"   目标时间: {target_datetime}")
        print(f"   模式数据中的时间值数量: {len(time_values)}")
        
        # 转换时间值为datetime对象进行比较
        target_datetime_np = np.datetime64(target_datetime)
        
        # 查找最接近的时间索引
        dateind = np.argmin(np.abs(time_values - target_datetime_np))
        closest_time = time_values[dateind]
        print(f"   最接近的时间值: {closest_time}")
        print(f"   对应的索引: {dateind}")
        
        # 构建变量名（提前48小时和24小时预报）
        MFhour = 48
        MFhour2 = MFhour - 24
        TPname1 = f"tppm{MFhour:03d}"
        TPname2 = f"tppm{MFhour2:03d}"
        
        # 读取数据并截取区域
        Mdata1 = fecmwfthintp[TPname1].isel(time=dateind).sel(
            lat=slice(lats, latn),
            lon=slice(lons, lonn)
        )
        Mdata2 = fecmwfthintp[TPname2].isel(time=dateind).sel(
            lat=slice(lats, latn),
            lon=slice(lons, lonn)
        )
        
        # 计算24小时降水量
        rain_data = Mdata1 - Mdata2
        
        # 单位转换（从米转换为毫米）
        rain_data = rain_data * 1000
        
        # 复制坐标
        rain_data.attrs['units'] = "24h Precipitation (mm)"
        
        # 确保数据是2D的（lat, lon）
        if len(rain_data.shape) > 2:
            # 如果有多余维度，压缩维度
            rain_data = rain_data.squeeze()
        
        fecmwfthintp.close()
        
        print("✅ 成功读取EC模式降水数据")
        print(f"   降水数据形状: {rain_data.shape}")
        print(f"   降水数据维度: {rain_data.dims}")
        
        return rain_data
        
    except Exception as e:
        print(f"❌ 读取EC模式数据出错: {e}")
        return None

# 读取日期文件
def read_dates_from_file():
    # 日期文件路径
    date_file_path = "/mnt/f/文章-1/data/暖区暴雨日期/2023-2025年前汛期暖区暴雨日期.txt"
    
    dates = []
    
    try:
        with open(date_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # 提取第一列数据
                    parts = line.split()
                    if parts:
                        date_str = parts[0]
                        # 提取前8位作为日期（YYYYMMDD格式）
                        if len(date_str) >= 8 and date_str[:8].isdigit():
                            dates.append(date_str[:8])
        
        print(f"✅ 成功读取 {len(dates)} 个日期")
        print(f"   前5个日期: {dates[:5]}")
        return dates
    except Exception as e:
        print(f"❌ 读取日期文件时出错: {e}")
        return []

# 计算混淆矩阵和站点状态
def calculate_confusion_matrix(obs_rainfall, model_rainfall, threshold=50):
    """
    计算混淆矩阵和站点状态
    
    参数:
        obs_rainfall: 观测降水量数组
        model_rainfall: 模式预报降水量数组
        threshold: 暴雨阈值（默认50mm）
    
    返回:
        hit: 命中数量
        false_alarm: 空报数量
        miss: 漏报数量
        correct_negative: 正确否定数量
        status: 每个站点的状态（0: 正确否定, 1: 命中, 2: 空报, 3: 漏报）
        status_details: 详细的状态信息，包括站点ID、经纬度、观测和预报值
    """
    # 初始化状态数组和详细信息列表
    status = []
    status_details = []
    
    # 计算每个站点的状态
    for i, station in enumerate(obs_rainfall):
        station_id = station['station_id']
        lon = station['longitude']
        lat = station['latitude']
        obs_val = station['rainfall']
        model_val = model_rainfall[i] if i < len(model_rainfall) else 0
        
        # 处理缺测值
        if np.isnan(obs_val) or np.isnan(model_val):
            continue
        
        # 确定状态
        if obs_val > threshold and model_val > threshold:
            status_code = 1  # 命中
        elif obs_val <= threshold and model_val > threshold:
            status_code = 2  # 空报
        elif obs_val > threshold and model_val <= threshold:
            status_code = 3  # 漏报
        else:
            status_code = 0  # 正确否定
        
        status.append(status_code)
        status_details.append({
            'station_id': station_id,
            'longitude': lon,
            'latitude': lat,
            'observed': obs_val,
            'forecast': model_val,
            'status': status_code
        })
    
    # 计算混淆矩阵
    hit = status.count(1)
    false_alarm = status.count(2)
    miss = status.count(3)
    correct_negative = status.count(0)
    
    return hit, false_alarm, miss, correct_negative, status, status_details

# 处理单个日期的数据
def process_single_date(date_str):
    print(f"\n=======================================")
    print(f"处理日期: {date_str}")
    print(f"=======================================")
    
    # 读取站点降水数据
    station_data = read_station_rainfall(date_str)
    
    if not station_data:
        print(f"   没有站点数据")
        return None
    
    # 读取EC模式降水数据（提前48小时预报）
    print("\n📊 读取EC模式降水数据:")
    ec_rain_data = read_ec_rainfall(date_str)
    
    if ec_rain_data is None:
        print("   EC模式数据读取失败")
        return None
    
    # 插值数据到站点
    print("\n📊 插值数据到站点:")
    print(f"   站点数量: {len(station_data)}")
    print(f"   降水数据形状: {ec_rain_data.shape}")
    print(f"   降水数据维度: {ec_rain_data.dims}")
    
    interpolated_stations = interpolate_data_to_stations(station_data, ec_rain_data, 'forecast')
    
    if not interpolated_stations:
        print("   插值失败")
        return None
    
    print(f"   插值后站点数量: {len(interpolated_stations)}")
    
    # 提取预报值
    forecast_values = []
    for i, station in enumerate(interpolated_stations):
        try:
            forecast = station.get('forecast', 0)
            # 检查是否为None
            if forecast is None:
                forecast = 0
            # 检查是否为NaN
            if isinstance(forecast, (np.ndarray, list)):
                # 如果是数组或列表，取第一个元素
                forecast = forecast[0] if len(forecast) > 0 else 0
            # 尝试转换为浮点数
            forecast = float(forecast)
            # 检查是否为NaN
            if np.isnan(forecast):
                forecast = 0
            forecast_values.append(forecast)
        except Exception as e:
            print(f"   处理站点 {i} 时出错: {e}")
            forecast_values.append(0)
    
    # 计算混淆矩阵
    print("\n📊 计算混淆矩阵:")
    hit, false_alarm, miss, correct_negative, status, status_details = calculate_confusion_matrix(
        station_data, forecast_values
    )
    
    # 打印统计结果
    print(f"   命中（H）: {hit}")
    print(f"   空报（F）: {false_alarm}")
    print(f"   漏报（M）: {miss}")
    print(f"   正确否定（N）: {correct_negative}")
    
    return {
        'date': date_str,
        'hit': hit,
        'false_alarm': false_alarm,
        'miss': miss,
        'correct_negative': correct_negative,
        'status_details': status_details
    }

# 主函数
def main():
    print("开始处理数据...")
    
    # 读取日期文件
    dates_to_process = read_dates_from_file()
    
    if not dates_to_process:
        print("❌ 没有读取到日期数据，程序结束")
        return
    
    # 处理每个日期
    print(f"\n=======================================")
    print(f"开始处理 {len(dates_to_process)} 个日期")
    print(f"=======================================")
    
    # 收集所有统计信息
    all_stats = []
    
    for i, date_str in enumerate(dates_to_process):
        print(f"\n📅 处理进度: {i+1}/{len(dates_to_process)}")
        print(f"📅 当前处理日期: {date_str}")
        
        # 处理单个日期
        start_time = datetime.now()
        
        # 调用process_single_date函数处理数据
        result = process_single_date(date_str)
        
        if result:
            all_stats.append(result)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        print(f"\n📅 处理时间: {processing_time:.2f} 秒")
    
    # 保存统计信息到文件
    print("\n=======================================")
    print("保存统计信息到文件")
    print("=======================================")
    
    # 创建输出目录
    output_dir = r"/mnt/f/文章-1/data/processed"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 保存统计摘要
    summary_file = os.path.join(output_dir, f"forecast_verification_summary_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
    details_file = os.path.join(output_dir, f"forecast_verification_details_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
    
    try:
        # 写入摘要文件
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("日期,H,F,M,N\n")
            for stat in all_stats:
                f.write(f"{stat['date']},{stat['hit']},{stat['false_alarm']},{stat['miss']},{stat['correct_negative']}\n")
        
        # 写入详细文件
        with open(details_file, 'w', encoding='utf-8') as f:
            f.write("日期,站点ID,经度,纬度,观测值,预报值,状态\n")
            for stat in all_stats:
                for detail in stat['status_details']:
                    status_label = {0: 'N', 1: 'H', 2: 'F', 3: 'M'}.get(detail['status'], 'N')
                    f.write(f"{stat['date']},{detail['station_id']},{detail['longitude']},{detail['latitude']},{detail['observed']},{detail['forecast']},{status_label}\n")
        
        print(f"✅ 统计摘要已保存到: {summary_file}")
        print(f"✅ 详细统计已保存到: {details_file}")
        
    except Exception as e:
        print(f"❌ 保存文件时出错: {e}")
    
    # 打印总统计
    print("\n=======================================")
    print("总统计")
    print("=======================================")
    
    total_hit = sum(stat['hit'] for stat in all_stats)
    total_false_alarm = sum(stat['false_alarm'] for stat in all_stats)
    total_miss = sum(stat['miss'] for stat in all_stats)
    total_correct_negative = sum(stat['correct_negative'] for stat in all_stats)
    
    print(f"总命中（H）: {total_hit}")
    print(f"总空报（F）: {total_false_alarm}")
    print(f"总漏报（M）: {total_miss}")
    print(f"总正确否定（N）: {total_correct_negative}")
    
    print("\n所有日期处理完成!")

if __name__ == "__main__":
    main()