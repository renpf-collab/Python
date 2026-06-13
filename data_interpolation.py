import numpy as np
from scipy.interpolate import RegularGridInterpolator

# 通用数据插值函数
def interpolate_data_to_stations(station_data, data, variable_name):
    """
    将气象数据插值到站点位置
    
    参数:
        station_data: 站点数据列表，每个站点包含'longitude'和'latitude'字段
        data: xarray.DataArray类型的气象数据
        variable_name: 变量名，用于在站点数据中存储插值结果
    
    返回:
        插值后的站点数据列表，每个站点添加了插值结果
    """
    if not station_data:
        print(f"❌ 站点数据为空，无法进行{variable_name}插值")
        return None
    
    if data is None:
        print(f"❌ {variable_name}数据为空，无法进行插值")
        return None
    
    try:
        # 提取站点的经纬度
        lons = [station['longitude'] for station in station_data]
        lats = [station['latitude'] for station in station_data]
        station_ids = [station['station_id'] for station in station_data]
        
        # 尝试识别经纬度维度
        lon_dim = None
        lat_dim = None
        
        # 常见的经纬度维度名称
        possible_lon_names = ['lon', 'longitude', 'x', 'X']
        possible_lat_names = ['lat', 'latitude', 'y', 'Y']
        
        # 检查坐标变量
        for coord in data.coords:
            if coord.lower() in [name.lower() for name in possible_lon_names]:
                lon_dim = coord
            elif coord.lower() in [name.lower() for name in possible_lat_names]:
                lat_dim = coord
        
        # 检查数据变量的维度
        if not lon_dim or not lat_dim:
            for dim in data.dims:
                if dim.lower() in [name.lower() for name in possible_lon_names]:
                    lon_dim = dim
                elif dim.lower() in [name.lower() for name in possible_lat_names]:
                    lat_dim = dim
        
        # 执行插值
        if lon_dim and lat_dim:
            # 提取数据数组和坐标（使用scipy插值，更可靠）
            try:
                # 提取数据数组和坐标
                data_array = data.values
                lon_array = data[lon_dim].values
                lat_array = data[lat_dim].values
                
                # 处理可能的额外维度（如果存在）
                # 数据虽然可能是多维的，但除了lat/lon外的维度只有一个层次
                while data_array.ndim > 2:
                    data_array = data_array[0] if len(data_array) > 0 else data_array.squeeze()
                
                # 检查经纬度数组是否排序
                if not np.array_equal(lat_array, np.sort(lat_array)):
                    sort_idx = np.argsort(lat_array)
                    lat_array = lat_array[sort_idx]
                    data_array = data_array[sort_idx, :]
                
                if not np.array_equal(lon_array, np.sort(lon_array)):
                    sort_idx = np.argsort(lon_array)
                    lon_array = lon_array[sort_idx]
                    data_array = data_array[:, sort_idx]
                
                # 创建插值函数，设置bounds_error=False以处理边界情况
                interpolator = RegularGridInterpolator(
                    (lat_array, lon_array),  # 注意顺序：lat在前，lon在后
                    data_array,
                    method='linear',
                    bounds_error=False,
                    fill_value=np.nan  # 超出范围的点返回NaN
                )
                
                # 准备插值点
                points = list(zip(lats, lons))
                
                # 执行插值
                data_values = interpolator(points)
                
                # 检查插值结果长度是否与站点数量匹配
                if len(data_values) != len(station_data):
                    print(f"⚠️ 插值结果长度({len(data_values)})与站点数量({len(station_data)})不匹配，使用最小长度")
                    min_len = min(len(data_values), len(station_data))
                    data_values = data_values[:min_len]
                    station_data = station_data[:min_len]
                
                # 将插值结果添加到站点数据中
                interpolated_stations = []
                for i, station in enumerate(station_data):
                    station_copy = station.copy()
                    data_val = data_values[i]
                    # 处理NaN值
                    if np.isnan(data_val):
                        station_copy[variable_name] = None
                    else:
                        station_copy[variable_name] = data_val
                    interpolated_stations.append(station_copy)
                
                print(f"✅ 成功将{variable_name}数据插值到 {len(interpolated_stations)} 个站点")
                return interpolated_stations
                
            except Exception as e:
                print(f"❌ 插值失败: {e}")
                return None
        else:
            print("❌ 未找到经纬度维度，无法进行插值")
            return None
            
    except Exception as e:
        print(f"❌ 插值过程中出错: {e}")
        return None