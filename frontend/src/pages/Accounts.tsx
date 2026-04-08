import { useEffect, useState, useCallback } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, InputNumber, Switch,
  Tag, Space, Typography, Popconfirm, Tooltip, App, Collapse,
} from 'antd';
import {
  PlusOutlined, SyncOutlined, EditOutlined, DeleteOutlined,
  KeyOutlined, CheckOutlined, EyeOutlined, EyeInvisibleOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { accountApi } from '../api/client';

const { Title, Text, Paragraph } = Typography;

const providerOptions = [
  { value: 'qq', label: 'QQ邮箱' },
  { value: 'netease', label: '网易邮箱 (163/126)' },
  { value: 'outlook', label: 'Outlook / Hotmail' },
  { value: 'gmail', label: 'Gmail' },
];

const statusMap: Record<string, { color: string; text: string }> = {
  active: { color: 'green', text: '正常' },
  pending_manual: { color: 'orange', text: '待手动改密' },
  error: { color: 'red', text: '异常' },
  paused: { color: 'default', text: '已暂停' },
};

export default function Accounts() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [confirmAccount, setConfirmAccount] = useState<any>(null);
  const [passwordVisible, setPasswordVisible] = useState<Record<string, boolean>>({});
  const [passwords, setPasswords] = useState<Record<string, string>>({});
  const [search, setSearch] = useState('');
  const [filterProvider, setFilterProvider] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [form] = Form.useForm();
  const [confirmForm] = Form.useForm();
  const { message, modal } = App.useApp();

  const loadAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await accountApi.list({ search, provider_type: filterProvider, status: filterStatus });
      setAccounts(res.data);
    } catch {
      message.error('加载账号列表失败');
    } finally {
      setLoading(false);
    }
  }, [search, filterProvider, filterStatus]);

  useEffect(() => { loadAccounts(); }, [loadAccounts]);

  const openCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({
      auto_change_enabled: false,
      change_interval_days: 30,
      password_rule: { length: 16, uppercase: true, lowercase: true, digits: true, special: true },
    });
    setModalOpen(true);
  };

  const openEdit = (record: any) => {
    setEditingId(record.id);
    form.setFieldsValue({
      email: record.email,
      provider_type: record.provider_type,
      display_name: record.display_name,
      auto_change_enabled: record.auto_change_enabled,
      change_interval_days: record.change_interval_days,
      password_rule: record.password_rule || { length: 16, uppercase: true, lowercase: true, digits: true, special: true },
      notes: record.notes,
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingId) {
        const updateData: any = { ...values };
        delete updateData.email;
        delete updateData.provider_type;
        if (!updateData.password) delete updateData.password;
        await accountApi.update(editingId, updateData);
        message.success('更新成功');
      } else {
        await accountApi.create(values);
        message.success('添加成功');
      }
      setModalOpen(false);
      loadAccounts();
    } catch (err: any) {
      if (err.response?.data?.detail) {
        message.error(err.response.data.detail);
      }
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await accountApi.delete(id);
      message.success('已删除');
      loadAccounts();
    } catch {
      message.error('删除失败');
    }
  };

  const handleChangePassword = async (record: any) => {
    modal.confirm({
      title: '触发改密',
      content: `确定要触发 ${record.email} 的密码修改吗？系统将尝试自动修改，如遇到验证码等情况会提示你手动操作。`,
      onOk: async () => {
        try {
          await accountApi.changePassword(record.id);
          message.success('改密任务已提交，请稍后刷新查看结果');
          setTimeout(loadAccounts, 3000);
        } catch {
          message.error('触发改密失败');
        }
      },
    });
  };

  const openConfirm = (record: any) => {
    setConfirmAccount(record);
    confirmForm.resetFields();
    setConfirmModalOpen(true);
  };

  const handleConfirm = async () => {
    if (!confirmAccount) return;
    try {
      const values = await confirmForm.validateFields();
      await accountApi.confirmChange(confirmAccount.id, values.new_password);
      message.success('已确认密码修改');
      setConfirmModalOpen(false);
      loadAccounts();
    } catch (err: any) {
      if (err.response?.data?.detail) {
        message.error(err.response.data.detail);
      }
    }
  };

  const togglePassword = async (id: string) => {
    if (passwordVisible[id]) {
      setPasswordVisible(prev => ({ ...prev, [id]: false }));
      return;
    }
    try {
      const res = await accountApi.getPassword(id);
      setPasswords(prev => ({ ...prev, [id]: res.data.current_password }));
      setPasswordVisible(prev => ({ ...prev, [id]: true }));
    } catch {
      message.error('获取密码失败');
    }
  };

  const copyPassword = async (id: string) => {
    let pwd = passwords[id];
    if (!pwd) {
      try {
        const res = await accountApi.getPassword(id);
        pwd = res.data.current_password;
        setPasswords(prev => ({ ...prev, [id]: pwd }));
      } catch {
        message.error('获取密码失败');
        return;
      }
    }
    await navigator.clipboard.writeText(pwd);
    message.success('密码已复制到剪贴板');
  };

  const columns = [
    {
      title: '邮箱', dataIndex: 'email', key: 'email',
      render: (v: string, r: any) => (
        <div>
          <div>{v}</div>
          {r.display_name && <Text type="secondary" style={{ fontSize: 12 }}>{r.display_name}</Text>}
        </div>
      ),
    },
    {
      title: '类型', dataIndex: 'provider_type', key: 'type',
      render: (v: string) => providerOptions.find(p => p.value === v)?.label || v,
    },
    {
      title: '当前密码', key: 'password', width: 200,
      render: (_: any, r: any) => (
        <Space>
          <Text code style={{ minWidth: 100, display: 'inline-block' }}>
            {passwordVisible[r.id] ? passwords[r.id] : '••••••••'}
          </Text>
          <Tooltip title={passwordVisible[r.id] ? '隐藏' : '查看'}>
            <Button
              type="text"
              size="small"
              icon={passwordVisible[r.id] ? <EyeInvisibleOutlined /> : <EyeOutlined />}
              onClick={() => togglePassword(r.id)}
            />
          </Tooltip>
          <Tooltip title="复制">
            <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyPassword(r.id)} />
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => {
        const info = statusMap[s] || { color: 'default', text: s };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '自动改密', dataIndex: 'auto_change_enabled', key: 'auto',
      render: (v: boolean, r: any) => v ? (
        <Tooltip title={`每 ${r.change_interval_days} 天`}>
          <Tag color="blue">已开启</Tag>
        </Tooltip>
      ) : <Tag>未开启</Tag>,
    },
    {
      title: '下次改密', dataIndex: 'next_password_change', key: 'next',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-',
    },
    {
      title: '操作', key: 'actions', width: 200,
      render: (_: any, r: any) => (
        <Space size="small">
          {r.status === 'pending_manual' ? (
            <Tooltip title="确认已手动改密">
              <Button type="primary" size="small" icon={<CheckOutlined />} onClick={() => openConfirm(r)} />
            </Tooltip>
          ) : (
            <Tooltip title="触发改密">
              <Button size="small" icon={<KeyOutlined />} onClick={() => handleChangePassword(r)} />
            </Tooltip>
          )}
          <Tooltip title="编辑">
            <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          </Tooltip>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
            <Tooltip title="删除">
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>邮箱账号</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>添加账号</Button>
      </div>

      <Space style={{ marginBottom: 16 }} wrap>
        <Input.Search
          placeholder="搜索邮箱"
          allowClear
          onSearch={setSearch}
          style={{ width: 240 }}
        />
        <Select
          placeholder="邮箱类型"
          allowClear
          options={providerOptions}
          onChange={(v) => setFilterProvider(v || '')}
          style={{ width: 180 }}
        />
        <Select
          placeholder="状态"
          allowClear
          options={[
            { value: 'active', label: '正常' },
            { value: 'pending_manual', label: '待手动改密' },
            { value: 'error', label: '异常' },
            { value: 'paused', label: '已暂停' },
          ]}
          onChange={(v) => setFilterStatus(v || '')}
          style={{ width: 140 }}
        />
        <Button icon={<SyncOutlined />} onClick={loadAccounts}>刷新</Button>
      </Space>

      <Table
        dataSource={accounts}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `共 ${t} 个账号` }}
      />

      <Modal
        title={editingId ? '编辑账号' : '添加账号'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        width={560}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          {!editingId && (
            <>
              <Form.Item name="email" label="邮箱地址" rules={[{ required: true, message: '请输入邮箱' }]}>
                <Input placeholder="example@qq.com" />
              </Form.Item>
              <Form.Item name="provider_type" label="邮箱类型" rules={[{ required: true, message: '请选择类型' }]}>
                <Select options={providerOptions} placeholder="选择邮箱类型" />
              </Form.Item>
              <Form.Item name="password" label="当前密码" rules={[{ required: true, message: '请输入当前密码' }]}>
                <Input.Password placeholder="输入当前邮箱密码" />
              </Form.Item>
            </>
          )}
          {editingId && (
            <Form.Item name="password" label="更新密码（留空不修改）">
              <Input.Password placeholder="输入新密码，留空则不修改" />
            </Form.Item>
          )}
          <Form.Item name="display_name" label="备注名称">
            <Input placeholder="如：工作邮箱、个人邮箱" />
          </Form.Item>
          <Form.Item name="auto_change_enabled" label="自动改密" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="change_interval_days" label="改密周期（天）">
            <InputNumber min={1} max={365} style={{ width: '100%' }} />
          </Form.Item>

          <Collapse
            items={[{
              key: 'rule',
              label: '密码生成规则',
              children: (
                <>
                  <Form.Item name={['password_rule', 'length']} label="密码长度">
                    <InputNumber min={8} max={64} style={{ width: '100%' }} />
                  </Form.Item>
                  <Space wrap>
                    <Form.Item name={['password_rule', 'uppercase']} valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch checkedChildren="大写" unCheckedChildren="大写" />
                    </Form.Item>
                    <Form.Item name={['password_rule', 'lowercase']} valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch checkedChildren="小写" unCheckedChildren="小写" />
                    </Form.Item>
                    <Form.Item name={['password_rule', 'digits']} valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch checkedChildren="数字" unCheckedChildren="数字" />
                    </Form.Item>
                    <Form.Item name={['password_rule', 'special']} valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch checkedChildren="特殊字符" unCheckedChildren="特殊字符" />
                    </Form.Item>
                  </Space>
                </>
              ),
            }]}
            style={{ marginBottom: 16 }}
          />

          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} placeholder="可选备注信息" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="确认手动改密"
        open={confirmModalOpen}
        onOk={handleConfirm}
        onCancel={() => setConfirmModalOpen(false)}
        destroyOnClose
      >
        <Paragraph>
          请确认你已在 <Text strong>{confirmAccount?.email}</Text> 的服务商网站上手动修改了密码。
        </Paragraph>
        <Form form={confirmForm} layout="vertical">
          <Form.Item
            name="new_password"
            label="新密码（如果你使用了系统生成的密码可留空）"
          >
            <Input.Password placeholder="如使用了自定义密码请在此输入" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
