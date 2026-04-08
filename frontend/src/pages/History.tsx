import { useEffect, useState, useCallback } from 'react';
import {
  Table, Tag, Select, Space, Typography, Button, Modal, Descriptions, App,
} from 'antd';
import { SyncOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { historyApi, accountApi } from '../api/client';

const { Title, Text } = Typography;

const statusMap: Record<string, { color: string; text: string }> = {
  success: { color: 'green', text: '成功' },
  failed: { color: 'red', text: '失败' },
  pending: { color: 'orange', text: '待确认' },
};

export default function History() {
  const [records, setRecords] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterAccount, setFilterAccount] = useState('');
  const [accounts, setAccounts] = useState<any[]>([]);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const { message } = App.useApp();

  useEffect(() => {
    accountApi.list().then(res => setAccounts(res.data)).catch(() => {});
  }, []);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: pageSize };
      if (filterStatus) params.status = filterStatus;
      if (filterAccount) params.account_id = filterAccount;

      const [listRes, countRes] = await Promise.all([
        historyApi.list(params),
        historyApi.count(params),
      ]);
      setRecords(listRes.data);
      setTotal(countRes.data.total);
    } catch {
      message.error('加载变更历史失败');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filterStatus, filterAccount]);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const showDetail = async (id: string) => {
    setDetail(null);
    setDetailLoading(true);
    setDetailOpen(true);
    try {
      const res = await historyApi.getDetail(id);
      setDetail(res.data);
    } catch {
      message.error('获取详情失败');
      setDetailOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const columns = [
    { title: '邮箱', dataIndex: 'account_email', key: 'email' },
    {
      title: '方式', dataIndex: 'change_method', key: 'method',
      render: (v: string) => v === 'auto' ? <Tag color="blue">自动</Tag> : <Tag>手动</Tag>,
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => {
        const info = statusMap[s] || { color: 'default', text: s };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '错误信息', dataIndex: 'error_message', key: 'error',
      ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: '时间', dataIndex: 'created_at', key: 'time',
      render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作', key: 'actions', width: 80,
      render: (_: any, r: any) => (
        <Button size="small" icon={<EyeOutlined />} onClick={() => showDetail(r.id)}>详情</Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>变更历史</Title>

      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          placeholder="筛选邮箱"
          allowClear
          showSearch
          optionFilterProp="label"
          options={accounts.map((a: any) => ({ value: a.id, label: a.email }))}
          onChange={(v) => { setFilterAccount(v || ''); setPage(1); }}
          style={{ width: 260 }}
        />
        <Select
          placeholder="状态"
          allowClear
          options={[
            { value: 'success', label: '成功' },
            { value: 'failed', label: '失败' },
            { value: 'pending', label: '待确认' },
          ]}
          onChange={(v) => { setFilterStatus(v || ''); setPage(1); }}
          style={{ width: 140 }}
        />
        <Button icon={<SyncOutlined />} onClick={loadHistory}>刷新</Button>
      </Space>

      <Table
        dataSource={records}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showTotal: (t) => `共 ${t} 条记录`,
          onChange: (p, ps) => { setPage(p); setPageSize(ps); },
        }}
      />

      <Modal
        title="变更详情"
        open={detailOpen}
        onCancel={() => { setDetailOpen(false); setDetail(null); }}
        footer={null}
        width={500}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : detail ? (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="邮箱">{detail.account_email}</Descriptions.Item>
            <Descriptions.Item label="方式">{detail.change_method === 'auto' ? '自动' : '手动'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusMap[detail.status]?.color}>{statusMap[detail.status]?.text}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="旧密码">
              <Text code>{detail.old_password || '-'}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="新密码">
              <Text code>{detail.new_password || '-'}</Text>
            </Descriptions.Item>
            {detail.error_message && (
              <Descriptions.Item label="错误信息">
                <Text type="danger">{detail.error_message}</Text>
              </Descriptions.Item>
            )}
            <Descriptions.Item label="时间">
              {dayjs(detail.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          </Descriptions>
        ) : null}
      </Modal>
    </div>
  );
}
