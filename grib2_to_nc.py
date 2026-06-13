#!/usr/bin/env python3
"""GRIB2 转 NetCDF 工具，支持多种层级类型"""

import sys
import xarray as xr

def grib2_to_nc(input_file):
    """将 GRIB2 文件转换为 NetCDF"""
    print(f"正在读取 GRIB2 文件: {input_file}")
    
    # 尝试直接读取
    try:
        ds = xr.open_dataset(input_file, engine='cfgrib')
        output_file = input_file.replace('.grib2', '.nc')
        ds.to_netcdf(output_file)
        print(f"✅ 转换成功: {output_file}")
        print(f"📊 变量列表: {list(ds.data_vars.keys())}")
        ds.close()
        return True
    except Exception as e:
        # 如果遇到多个层级类型的问题
        if "multiple values for unique key" in str(e):
            print("⚠️ 检测到多个层级类型，正在尝试分别转换...")
            
            # 常见的层级类型
            level_types = [
                {'typeOfLevel': 'surface'},
                {'typeOfLevel': 'isobaricInhPa'},
                {'typeOfLevel': 'heightAboveGround'},
                {'typeOfLevel': 'meanSea'},
                {'typeOfLevel': 'entireAtmosphere'},
                {'typeOfLevel': 'soilLayer'},
                {'typeOfLevel': 'nominalTop'},
                {'typeOfLevel': 'mostUnstableParcel'},
            ]
            
            for filter_keys in level_types:
                try:
                    print(f"  尝试: {filter_keys}")
                    ds = xr.open_dataset(
                        input_file, 
                        engine='cfgrib',
                        backend_kwargs={'filter_by_keys': filter_keys}
                    )
                    
                    level_name = filter_keys['typeOfLevel']
                    output_file = f"{input_file.replace('.grib2', '')}_{level_name}.nc"
                    ds.to_netcdf(output_file)
                    print(f"    ✅ 转换成功: {output_file}")
                    print(f"       变量: {list(ds.data_vars.keys())}")
                    ds.close()
                except Exception as e2:
                    print(f"    ❌ 失败: {str(e2)[:50]}")
            
            print("\n📝 转换完成！")
            return True
        else:
            print(f"❌ 转换失败: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python grib2_to_nc.py <input.grib2>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    grib2_to_nc(input_file)