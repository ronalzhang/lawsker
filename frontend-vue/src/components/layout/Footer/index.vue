<template>
  <footer class="lk-footer">
    <div class="lk-footer__container">
      <!-- 主要内容区 -->
      <div class="lk-footer__main" v-if="showMain">
        <div class="lk-footer__section">
          <h4 class="lk-footer__title">关于律思客</h4>
          <ul class="lk-footer__links">
            <li><a href="/about" @click.prevent="handleLinkClick('/about')">关于我们</a></li>
            <li><a href="/contact" @click.prevent="handleLinkClick('/contact')">联系我们</a></li>
            <li><a href="/careers" @click.prevent="handleLinkClick('/careers')">加入我们</a></li>
            <li><a href="/news" @click.prevent="handleLinkClick('/news')">新闻动态</a></li>
          </ul>
        </div>

        <div class="lk-footer__section">
          <h4 class="lk-footer__title">服务支持</h4>
          <ul class="lk-footer__links">
            <li><a href="/help" @click.prevent="handleLinkClick('/help')">帮助中心</a></li>
            <li><a href="/faq" @click.prevent="handleLinkClick('/faq')">常见问题</a></li>
            <li><a href="/feedback" @click.prevent="handleLinkClick('/feedback')">意见反馈</a></li>
            <li><a href="/api" @click.prevent="handleLinkClick('/api')">开发者API</a></li>
          </ul>
        </div>

        <div class="lk-footer__section">
          <h4 class="lk-footer__title">法律条款</h4>
          <ul class="lk-footer__links">
            <li><a href="/terms" @click.prevent="handleLinkClick('/terms')">服务条款</a></li>
            <li><a href="/privacy" @click.prevent="handleLinkClick('/privacy')">隐私政策</a></li>
            <li><a href="/disclaimer" @click.prevent="handleLinkClick('/disclaimer')">免责声明</a></li>
            <li><a href="/copyright" @click.prevent="handleLinkClick('/copyright')">版权声明</a></li>
          </ul>
        </div>

        <div class="lk-footer__section">
          <h4 class="lk-footer__title">关注我们</h4>
          <div class="lk-footer__social">
            <a href="#" class="lk-footer__social-link" @click.prevent="handleSocialClick('wechat')">
              <el-icon><ChatDotRound /></el-icon>
              <span>微信</span>
            </a>
            <a href="#" class="lk-footer__social-link" @click.prevent="handleSocialClick('weibo')">
              <el-icon><Share /></el-icon>
              <span>微博</span>
            </a>
            <a href="#" class="lk-footer__social-link" @click.prevent="handleSocialClick('qq')">
              <el-icon><ChatRound /></el-icon>
              <span>QQ</span>
            </a>
          </div>
          
          <div class="lk-footer__contact" v-if="showContact">
            <div class="lk-footer__contact-item">
              <el-icon><Phone /></el-icon>
              <span>{{ contactPhone }}</span>
            </div>
            <div class="lk-footer__contact-item">
              <el-icon><Message /></el-icon>
              <span>{{ contactEmail }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 分隔线 -->
      <el-divider v-if="showMain && showBottom" />

      <!-- 底部信息 -->
      <div class="lk-footer__bottom" v-if="showBottom">
        <div class="lk-footer__copyright">
          <span>© {{ currentYear }} 律思客 Lawsker. {{ copyrightText }}</span>
        </div>
        
        <div class="lk-footer__info">
          <span v-if="icp">{{ icp }}</span>
          <span v-if="license">{{ license }}</span>
        </div>

        <div class="lk-footer__links-inline" v-if="bottomLinks.length">
          <a
            v-for="(link, index) in bottomLinks"
            :key="index"
            :href="link.href"
            @click.prevent="handleLinkClick(link.href)"
          >
            {{ link.text }}
          </a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElIcon, ElDivider } from 'element-plus'
import {
  ChatDotRound,
  Share,
  ChatRound,
  Phone,
  Message
} from '@element-plus/icons-vue'

interface BottomLink {
  text: string
  href: string
}

interface Props {
  showMain?: boolean
  showBottom?: boolean
  showContact?: boolean
  contactPhone?: string
  contactEmail?: string
  copyrightText?: string
  icp?: string
  license?: string
  bottomLinks?: BottomLink[]
}

const props = withDefaults(defineProps<Props>(), {
  showMain: true,
  showBottom: true,
  showContact: true,
  contactPhone: '400-123-4567',
  contactEmail: 'contact@lawsker.com',
  copyrightText: '保留所有权利',
  icp: '京ICP备12345678号',
  license: '京公网安备11010802012345号',
  bottomLinks: () => [
    { text: '网站地图', href: '/sitemap' },
    { text: '友情链接', href: '/links' },
    { text: '合作伙伴', href: '/partners' }
  ]
})

const emit = defineEmits<{
  'link-click': [href: string]
  'social-click': [platform: string]
}>()

const router = useRouter()

const currentYear = computed(() => new Date().getFullYear())

const handleLinkClick = (href: string) => {
  emit('link-click', href)
  
  // 如果是内部链接，使用路由导航
  if (href.startsWith('/')) {
    router.push(href)
  } else {
    // 外部链接，在新窗口打开
    window.open(href, '_blank')
  }
}

const handleSocialClick = (platform: string) => {
  emit('social-click', platform)
  
  // 这里可以添加具体的社交媒体链接逻辑
  const socialLinks = {
    wechat: '#', // 可以显示二维码弹窗
    weibo: 'https://weibo.com/lawsker',
    qq: '#' // 可以显示QQ群号
  }
  
  const link = socialLinks[platform as keyof typeof socialLinks]
  if (link && link !== '#') {
    window.open(link, '_blank')
  }
}
</script>

<style scoped lang="scss">
.lk-footer {
  background: var(--el-bg-color-page);
  border-top: 1px solid var(--el-border-color-light);
  margin-top: auto;

  .lk-footer__container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px 20px;
  }

  .lk-footer__main {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 40px;
    margin-bottom: 20px;

    .lk-footer__section {
      .lk-footer__title {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .lk-footer__links {
        list-style: none;
        padding: 0;
        margin: 0;

        li {
          margin-bottom: 8px;

          a {
            color: var(--el-text-color-regular);
            text-decoration: none;
            font-size: 14px;
            transition: color 0.3s;

            &:hover {
              color: var(--el-color-primary);
            }
          }

          &:last-child {
            margin-bottom: 0;
          }
        }
      }

      .lk-footer__social {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 20px;

        .lk-footer__social-link {
          display: flex;
          align-items: center;
          color: var(--el-text-color-regular);
          text-decoration: none;
          font-size: 14px;
          transition: color 0.3s;

          &:hover {
            color: var(--el-color-primary);
          }

          .el-icon {
            margin-right: 8px;
            font-size: 16px;
          }
        }
      }

      .lk-footer__contact {
        .lk-footer__contact-item {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
          color: var(--el-text-color-regular);
          font-size: 14px;

          .el-icon {
            margin-right: 8px;
            color: var(--el-text-color-secondary);
          }

          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
  }

  .lk-footer__bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    padding-top: 20px;
    font-size: 14px;
    color: var(--el-text-color-secondary);

    .lk-footer__copyright {
      flex: 1;
    }

    .lk-footer__info {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;

      span {
        white-space: nowrap;
      }
    }

    .lk-footer__links-inline {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;

      a {
        color: var(--el-text-color-secondary);
        text-decoration: none;
        white-space: nowrap;
        transition: color 0.3s;

        &:hover {
          color: var(--el-color-primary);
        }
      }
    }
  }

  :deep(.el-divider) {
    margin: 20px 0;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .lk-footer {
    .lk-footer__container {
      padding: 30px 16px 16px;
    }

    .lk-footer__main {
      grid-template-columns: repeat(2, 1fr);
      gap: 30px;
    }

    .lk-footer__bottom {
      flex-direction: column;
      align-items: flex-start;
      text-align: left;

      .lk-footer__copyright {
        order: 3;
        flex: none;
        width: 100%;
      }

      .lk-footer__info {
        order: 1;
        flex-direction: column;
        gap: 8px;
      }

      .lk-footer__links-inline {
        order: 2;
        width: 100%;
      }
    }
  }
}

@media (max-width: 480px) {
  .lk-footer {
    .lk-footer__main {
      grid-template-columns: 1fr;
      gap: 24px;
    }

    .lk-footer__bottom {
      .lk-footer__links-inline {
        flex-direction: column;
        gap: 8px;
      }
    }
  }
}
</style>