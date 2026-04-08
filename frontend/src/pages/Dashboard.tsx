import { useEffect, useState } from 'react';
import { Button, Card, Col, Row, Statistic, Table, Tag, Typography, Spin, App } from 'antd';
import {
  MailOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { dashboardApi } from '../api/client';

const { Title } = Typography;

const statusMap: Record<string, { color: string; text: string }> = {
  active: { color: 'green', text: '正常' },
  pending_manual: { color: 'orange', text: '待手动改密' },
  error: { color: 'red', text: '异常' },
  paused: { color: 'default', text: '已暂停' },
};

const historyStatusMap: Record<string, { color: string; text: string }> = {
  success: { color: 'green', text: '成功' },
  failed: { color: 'red', text: '失败' },
  pending: { color: 'orange', text: '待确认' },
};

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState(false);
  const { message } = App.useApp();

  const loadData = () => {
    setLoading(true);
    setError(false);
    dashboardApi.get()
      .then(res => setData(res.data))
      .catch(() => { message.error('加载仪表盘数据失败'); setError(true); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadData(); }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (error || !data) return (
    <div style={{ textAlign: 'center', padding: 80 }}>
      <Typography.Text type="secondary">加载失败</Typography.Text>
      <br /><br />
      <Button onClick={loadData}>重试</Button>
    </div>
  );

  const { stats, expiring_accounts, pending_accounts, recent_history } = data;

  const statCards = [
    { title: '邮箱总数', value: stats.total_accounts, icon: <MailOutlined />, color: '#1677ff' },
    { title: '自动改密', value: stats.auto_change_enabled, icon: <SyncOutlined />, color: '#52c41a' },
    { title: '待手动处理', value: stats.pending_manual, icon: <ExclamationCircleOutlined />, color: '#faad14' },
    { title: '即将到期', value: stats.expiring_soon, icon: <ClockCircleOutlined />, color: '#ff4d4f' },
    { title: '近7天成功', value: stats.recent_success, icon: <CheckCircleOutlined />, color: '#52c41a' },
    { title: '近7天失败', value: stats.recent_failed, icon: <WarningOutlined />, color: '#ff4d4f' },
  ];

  const accountColumns = [
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => {
        const info = statusMap[s] || { color: 'default', text: s };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '下次改密', dataIndex: 'next_password_change', key: 'next',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
    },
  ];

  const historyColumns = [
    { title: '邮箱', dataIndex: 'account_email', key: 'email' },
    {
      title: '方式', dataIndex: 'change_method', key: 'method',
      render: (v: string) => v === 'auto' ? '自动' : '手动',
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => {
        const info = historyStatusMap[s] || { color: 'default', text: s };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '时间', dataIndex: 'created_at', key: 'time',
      render: (v: string) => dayjs(v).format('MM-DD HH:mm'),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>仪表盘</Title>

      <Row gutter={[16, 16]}>
        {statCards.map((card, i) => (
          <Col xs={12} sm={8} md={4} key={i}>
            <Card size="small" hoverable>
              <Statistic
                title={card.title}
                value={card.value}
                prefix={<span style={{ color: card.color }}>{card.icon}</span>}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="待手动处理" size="small" style={{ marginBottom: 16 }}>
            <Table
              dataSource={pending_accounts}
              columns={accountColumns}
              rowKey="id"
              size="small"
              pagination={false}
              locale={{ emptyText: '无待处理账号' }}
            />
          </Card>
          <Card title="即将到期" size="small">
            <Table
              dataSource={expiring_accounts}
              columns={accountColumns}
              rowKey="id"
              size="small"
              pagination={false}
              locale={{ emptyText: '暂无即将到期的账号' }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="最近变更记录" size="small">
            <Table
              dataSource={recent_history}
              columns={historyColumns}
              rowKey="id"
              size="small"
              pagination={false}
              locale={{ emptyText: '暂无记录' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
