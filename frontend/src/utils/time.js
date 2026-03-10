/**
 * 时间处理工具函数
 * 后端返回的时间是 UTC 时间（无时区信息），需要转换为本地时间
 */
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import utc from 'dayjs/plugin/utc'
import 'dayjs/locale/zh-cn'

// 加载插件
dayjs.extend(relativeTime)
dayjs.extend(utc)
dayjs.locale('zh-cn')

/**
 * 将 UTC 时间转换为本地时间并格式化为相对时间
 * @param {string} time - UTC 时间字符串
 * @returns {string} 相对时间（如：3小时前）
 */
export function formatRelativeTime(time) {
  if (!time) return ''
  // 后端返回的是 UTC 时间，使用 utc() 解析后转为本地时间
  return dayjs.utc(time).fromNow()
}

/**
 * 将 UTC 时间转换为本地时间并格式化为日期时间字符串
 * @param {string} time - UTC 时间字符串
 * @param {string} format - 格式化模板，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns {string} 格式化后的日期时间
 */
export function formatDateTime(time, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!time) return ''
  return dayjs.utc(time).local().format(format)
}

/**
 * 将 UTC 时间转换为本地时间并格式化为日期字符串
 * @param {string} time - UTC 时间字符串
 * @returns {string} 格式化后的日期
 */
export function formatDate(time) {
  if (!time) return ''
  return dayjs.utc(time).local().format('YYYY-MM-DD')
}

/**
 * 将 UTC 时间转换为本地时间
 * @param {string} time - UTC 时间字符串
 * @returns {dayjs.Dayjs} dayjs 对象
 */
export function toLocalTime(time) {
  if (!time) return null
  return dayjs.utc(time).local()
}

export default {
  formatRelativeTime,
  formatDateTime,
  formatDate,
  toLocalTime
}
