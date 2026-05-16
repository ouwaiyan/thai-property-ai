'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card, Typography, Space, Button, Input, Tag, Spin, App, Descriptions,
} from 'antd';
import {
  ArrowLeftOutlined, RobotOutlined, SendOutlined, ReloadOutlined,
} from '@ant-design/icons';
import { getLineConversation, getLineAIReply, replyLineMessage, pushLineMessage, getLead } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { LineConversationOut, LineMessageOut } from '@/types/line';
import type { LeadOut } from '@/types/lead';

const statusColor: Record<string, string> = {
  new: 'default', parsed: 'blue', in_progress: 'orange', pending_reply: 'red', contacted: 'green', closed: 'purple',
};

export default function LineConversationPage() {
  const { lineUserId } = useParams<{ lineUserId: string }>();
  const router = useRouter();
  const { message: msg } = App.useApp();
  const { t } = useI18n();

  const [conv, setConv] = useState<LineConversationOut | null>(null);
  const [lead, setLead] = useState<LeadOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [aiReply, setAiReply] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchData = () => {
    setLoading(true);
    getLineConversation(lineUserId)
      .then((data) => {
        setConv(data);
        if (data.lead_id) {
          getLead(data.lead_id).then(setLead).catch(() => {});
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [lineUserId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conv?.messages]);

  const handleAI = async () => {
    setAiLoading(true);
    try {
      const res = await getLineAIReply(lineUserId);
      setAiReply(res.suggested_reply);
      setReplyText(res.suggested_reply);
    } catch {
      msg.error(t('line.ai_reply_failed'));
    } finally {
      setAiLoading(false);
    }
  };

  const handleSend = async () => {
    if (!replyText.trim()) return;
    setSending(true);
    try {
      const latestIncoming = [...(conv?.messages || [])].reverse().find(
        (m: LineMessageOut) => m.direction === 'incoming' && m.reply_status !== 'replied'
      );
      const replyToken = (latestIncoming as { reply_token?: string } | undefined)?.reply_token;

      if (replyToken) {
        await replyLineMessage({ reply_token: replyToken, message_text: replyText });
      } else {
        await pushLineMessage({ line_user_id: lineUserId, message_text: replyText });
      }
      msg.success(t('line.send_success'));
      setReplyText('');
      setAiReply(null);
      fetchData();
    } catch {
      msg.error(t('line.send_failed'));
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }
  if (!conv) {
    return <div style={{ textAlign: 'center', padding: 100 }}>{t('line.conversation_not_found')}</div>;
  }

  const latestMsg = [...(conv.messages || [])].reverse().find(
    (m: LineMessageOut) => m.direction === 'incoming'
  );

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => router.push('/dashboard/line-review')}>
          {t('leads.back_to_list')}
        </Button>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>{t('leads.refresh')}</Button>
      </Space>

      {lead && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Descriptions size="small" column={3}>
            <Descriptions.Item label={t('line.customer')}>{lead.name}</Descriptions.Item>
            <Descriptions.Item label={t('common.status')}>
              <Tag color={statusColor[lead.status]}>{t(`status.${lead.status}`)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('leads.source')}>{lead.source}</Descriptions.Item>
            {lead.target_location && (
              <Descriptions.Item label={t('leads.target_location')}>{lead.target_location}</Descriptions.Item>
            )}
            {lead.budget_min && lead.budget_max && (
              <Descriptions.Item label={t('leads.budget_range')}>฿{lead.budget_min.toLocaleString()} - ฿{lead.budget_max.toLocaleString()}</Descriptions.Item>
            )}
            {lead.bedroom_count && (
              <Descriptions.Item label={t('properties.bedroom_count')}>{lead.bedroom_count}{t('properties.bedroom_unit', { n: lead.bedroom_count })}</Descriptions.Item>
            )}
          </Descriptions>
          <Button
            type="link"
            size="small"
            onClick={() => router.push(`/dashboard/leads/${lead.id}`)}
          >
            {t('leads.view_lead_detail')}
          </Button>
        </Card>
      )}

      <Card
        title={t('line.chat_history')}
        style={{ marginBottom: 16 }}
        bodyStyle={{ maxHeight: 400, overflow: 'auto', padding: 12 }}
      >
        {conv.messages.map((m) => (
          <div
            key={m.id}
            style={{
              marginBottom: 12,
              textAlign: m.direction === 'incoming' ? 'left' : 'right',
            }}
          >
            <div
              style={{
                display: 'inline-block',
                maxWidth: '75%',
                padding: '8px 14px',
                borderRadius: 12,
                backgroundColor: m.direction === 'incoming' ? '#f0f0f0' : '#1890ff',
                color: m.direction === 'incoming' ? '#000' : '#fff',
                textAlign: 'left',
              }}
            >
              <Typography.Text style={{ color: m.direction === 'incoming' ? '#000' : '#fff' }}>
                {m.message_text}
              </Typography.Text>
            </div>
            <div style={{ fontSize: 11, color: '#999', marginTop: 2 }}>
              {new Date(m.created_at).toLocaleString()}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </Card>

      {latestMsg && (
        <Card title={t('line.ai_suggest')} size="small" style={{ marginBottom: 16 }}>
          <Button
            icon={<RobotOutlined />}
            loading={aiLoading}
            onClick={handleAI}
            style={{ marginBottom: aiReply ? 12 : 0 }}
          >
            {t('line.ai_reply_btn')}
          </Button>
          {aiReply && (
            <div style={{
              background: '#f6ffed', border: '1px solid #b7eb8f',
              padding: 12, borderRadius: 8, marginTop: 12,
            }}>
              <Typography.Paragraph style={{ marginBottom: 8, whiteSpace: 'pre-wrap' }}>
                {aiReply}
              </Typography.Paragraph>
            </div>
          )}
        </Card>
      )}

      <Card title={t('line.send_reply')} size="small">
        <Input.TextArea
          rows={3}
          value={replyText}
          onChange={(e) => setReplyText(e.target.value)}
          placeholder={t('line.send_placeholder')}
          style={{ marginBottom: 12 }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          loading={sending}
          onClick={handleSend}
          disabled={!replyText.trim()}
        >
          {t('line.send')}
        </Button>
      </Card>
    </div>
  );
}
