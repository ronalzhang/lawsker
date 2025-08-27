/**
 * Gamification System for Lawsker
 * Handles lawyer level progression, points animation, and UI updates
 */

class GamificationSystem {
  constructor() {
    this.currentLevel = 1;
    this.currentPoints = 0;
    this.membershipMultiplier = 1;
    this.animationQueue = [];
    this.isAnimating = false;
    
    this.levelNames = {
      1: '见习律师',
      2: '初级律师', 
      3: '中级律师',
      4: '高级律师',
      5: '资深律师',
      6: '专家律师',
      7: '首席律师',
      8: '合伙人律师',
      9: '高级合伙人',
      10: '首席合伙人'
    };
    
    this.levelRequirements = {
      1: 0,
      2: 1000,
      3: 2500,
      4: 5000,
      5: 10000,
      6: 20000,
      7: 40000,
      8: 80000,
      9: 150000,
      10: 300000
    };
    
    this.init();
  }
  
  init() {
    this.bindEvents();
    this.loadUserData();
  }
  
  bindEvents() {
    // Listen for points updates
    document.addEventListener('pointsUpdated', (event) => {
      this.handlePointsUpdate(event.detail);
    });
    
    // Listen for level up events
    document.addEventListener('levelUp', (event) => {
      this.showLevelUpAnimation(event.detail);
    });
    
    // Listen for membership changes
    document.addEventListener('membershipChanged', (event) => {
      this.updateMembershipMultiplier(event.detail.multiplier);
    });
  }
  
  async loadUserData() {
    try {
      const response = await fetch('/api/v1/lawyer/level-details', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        this.updateLawyerLevel(data);
      }
    } catch (error) {
      console.error('Failed to load lawyer level data:', error);
    }
  }
  
  updateLawyerLevel(data) {
    this.currentLevel = data.current_level;
    this.currentPoints = data.level_points;
    this.membershipMultiplier = data.membership_multiplier || 1;
    
    this.renderLevelCard();
    this.updateProgressBar();
  }
  
  renderLevelCard() {
    const levelCard = document.querySelector('.lawyer-level-card');
    if (!levelCard) return;
    
    const levelBadge = levelCard.querySelector('.level-badge');
    const levelText = levelCard.querySelector('.level-text');
    const progressText = levelCard.querySelector('.progress-text');
    const multiplierElement = levelCard.querySelector('.membership-multiplier');
    
    if (levelBadge) {
      levelBadge.className = `level-badge level-${this.currentLevel}`;
    }
    
    if (levelText) {
      levelText.textContent = `${this.levelNames[this.currentLevel]} (${this.currentLevel}级)`;
    }
    
    if (progressText) {
      const nextLevel = Math.min(this.currentLevel + 1, 10);
      const nextLevelPoints = this.levelRequirements[nextLevel];
      const currentLevelPoints = this.levelRequirements[this.currentLevel];
      const progressPoints = this.currentPoints - currentLevelPoints;
      const requiredPoints = nextLevelPoints - currentLevelPoints;
      
      progressText.innerHTML = `
        <span class="progress-current">${progressPoints.toLocaleString()}</span>
        <span>/ ${requiredPoints.toLocaleString()}</span>
      `;
    }
    
    if (multiplierElement && this.membershipMultiplier > 1) {
      multiplierElement.style.display = 'flex';
      multiplierElement.querySelector('span').textContent = `${this.membershipMultiplier}x 积分倍数`;
    } else if (multiplierElement) {
      multiplierElement.style.display = 'none';
    }
  }
  
  updateProgressBar() {
    const progressFill = document.querySelector('.progress-fill');
    if (!progressFill) return;
    
    const nextLevel = Math.min(this.currentLevel + 1, 10);
    const nextLevelPoints = this.levelRequirements[nextLevel];
    const currentLevelPoints = this.levelRequirements[this.currentLevel];
    const progressPoints = this.currentPoints - currentLevelPoints;
    const requiredPoints = nextLevelPoints - currentLevelPoints;
    
    const percentage = Math.min((progressPoints / requiredPoints) * 100, 100);
    
    // Animate progress bar
    requestAnimationFrame(() => {
      progressFill.style.width = `${percentage}%`;
    });
  }
  
  handlePointsUpdate(pointsData) {
    const { points_earned, action, multiplier_applied } = pointsData;
    
    // Add to animation queue
    this.animationQueue.push({
      type: 'points',
      points: points_earned,
      action: action,
      multiplier: multiplier_applied
    });
    
    // Update current points
    this.currentPoints += points_earned;
    
    // Check for level up
    this.checkLevelUp();
    
    // Process animation queue
    this.processAnimationQueue();
  }
  
  checkLevelUp() {
    const nextLevel = this.currentLevel + 1;
    if (nextLevel <= 10 && this.currentPoints >= this.levelRequirements[nextLevel]) {
      // Level up!
      this.currentLevel = nextLevel;
      
      // Add level up animation to queue
      this.animationQueue.push({
        type: 'levelUp',
        newLevel: nextLevel,
        levelName: this.levelNames[nextLevel]
      });
      
      // Dispatch level up event
      document.dispatchEvent(new CustomEvent('levelUp', {
        detail: {
          newLevel: nextLevel,
          levelName: this.levelNames[nextLevel]
        }
      }));
    }
  }
  
  async processAnimationQueue() {
    if (this.isAnimating || this.animationQueue.length === 0) return;
    
    this.isAnimating = true;
    
    while (this.animationQueue.length > 0) {
      const animation = this.animationQueue.shift();
      
      if (animation.type === 'points') {
        await this.animatePointsGain(animation);
      } else if (animation.type === 'levelUp') {
        await this.showLevelUpAnimation(animation);
      }
      
      // Small delay between animations
      await this.delay(300);
    }
    
    this.isAnimating = false;
  }
  
  async animatePointsGain(animation) {
    const { points, action, multiplier } = animation;
    
    // Create enhanced floating points animation
    const pointsElement = document.createElement('div');
    pointsElement.className = 'floating-points-enhanced';
    pointsElement.innerHTML = `
      <div class="points-burst">
        <div class="points-value ${points > 0 ? 'points-positive' : 'points-negative'}">
          ${points > 0 ? '+' : ''}${points}
        </div>
        ${multiplier > 1 ? `<div class="points-multiplier">${multiplier}x 倍数</div>` : ''}
        <div class="points-action-label">${this.getActionLabel(action)}</div>
      </div>
      <div class="points-particles">
        ${Array.from({length: 8}, (_, i) => `<div class="particle particle-${i}"></div>`).join('')}
      </div>
    `;
    
    // Position near level card or action source
    const levelCard = document.querySelector('.lawyer-level-card');
    const actionElement = document.querySelector(`[data-action="${action}"]`);
    const targetElement = actionElement || levelCard;
    
    if (targetElement) {
      const rect = targetElement.getBoundingClientRect();
      pointsElement.style.position = 'fixed';
      pointsElement.style.left = `${rect.left + rect.width / 2 - 50}px`;
      pointsElement.style.top = `${rect.top + rect.height / 2 - 30}px`;
      pointsElement.style.zIndex = '1000';
      pointsElement.style.pointerEvents = 'none';
      
      document.body.appendChild(pointsElement);
      
      // Enhanced animation sequence
      pointsElement.style.animation = 'pointsBurst 3s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards';
      
      // Add screen shake effect for large point gains
      if (Math.abs(points) >= 200) {
        this.addScreenShakeEffect();
      }
      
      // Add sound effect
      this.playPointsSound(points > 0);
      
      // Remove after animation
      setTimeout(() => {
        if (pointsElement.parentNode) {
          pointsElement.parentNode.removeChild(pointsElement);
        }
      }, 3000);
    }
    
    // Update UI with smooth transitions
    this.renderLevelCard();
    this.updateProgressBarAnimated();
    
    return this.delay(800);
  }
  
  async showLevelUpAnimation(levelData) {
    const { newLevel, levelName } = levelData;
    
    // Create enhanced level up celebration
    const overlay = document.createElement('div');
    overlay.className = 'level-up-celebration-overlay';
    overlay.innerHTML = `
      <div class="celebration-container">
        <div class="celebration-fireworks">
          ${Array.from({length: 12}, (_, i) => `<div class="firework firework-${i}"></div>`).join('')}
        </div>
        
        <div class="celebration-main">
          <div class="celebration-icon-container">
            <div data-icon="trophy" class="celebration-icon"></div>
            <div class="celebration-glow"></div>
          </div>
          
          <div class="celebration-text-container">
            <div class="celebration-title">🎉 恭喜升级！ 🎉</div>
            <div class="celebration-level">${levelName}</div>
            <div class="celebration-level-number">等级 ${newLevel}</div>
            <div class="celebration-description">${this.getLevelDescription(newLevel)}</div>
          </div>
          
          <div class="celebration-rewards">
            <h4 class="rewards-title">🎁 解锁奖励</h4>
            <div class="rewards-list">
              ${this.getLevelRewards(newLevel).map(reward => `
                <div class="reward-item">
                  <div data-icon="${reward.icon}" class="reward-icon"></div>
                  <span class="reward-text">${reward.description}</span>
                </div>
              `).join('')}
            </div>
          </div>
          
          <div class="celebration-actions">
            <button class="btn btn-primary celebration-continue" onclick="this.parentElement.parentElement.parentElement.remove()">
              <div data-icon="arrow-right" style="width: 16px; height: 16px; margin-left: 8px;"></div>
              继续前进
            </button>
            <button class="btn btn-outline celebration-share" onclick="this.shareAchievement(${newLevel}, '${levelName}')">
              <div data-icon="share" style="width: 16px; height: 16px; margin-right: 8px;"></div>
              分享成就
            </button>
          </div>
        </div>
        
        <div class="celebration-confetti">
          ${Array.from({length: 50}, (_, i) => `<div class="confetti confetti-${i % 5}"></div>`).join('')}
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Replace icons
    if (window.IconSystem) {
      const icons = overlay.querySelectorAll('[data-icon]');
      icons.forEach(icon => {
        const iconName = icon.getAttribute('data-icon');
        window.IconSystem.replaceWithIcon(icon, iconName, {
          size: icon.classList.contains('celebration-icon') ? '80' : '20',
          className: icon.className
        });
      });
    }
    
    // Enhanced celebration effects
    this.triggerCelebrationEffects();
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
      if (overlay.parentNode) {
        overlay.remove();
      }
    }, 10000);
    
    // Play enhanced celebration sound
    this.playLevelUpCelebrationSound();
    
    // Add screen flash effect
    this.addScreenFlashEffect();
    
    return this.delay(2000);
  }
  
  playCelebrationSound() {
    // Create a simple celebration sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
      oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
      oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      // Ignore audio errors
    }
  }
  
  // Enhanced animation helper methods
  getActionLabel(action) {
    const actionLabels = {
      'case_complete_success': '案件完成',
      'case_complete_excellent': '优秀完成',
      'review_5star': '五星好评',
      'review_4star': '四星好评',
      'review_1star': '差评扣分',
      'review_2star': '差评扣分',
      'online_hour': '在线奖励',
      'ai_credit_used': 'AI使用',
      'payment_100yuan': '充值奖励',
      'case_declined': '拒绝案件',
      'late_response': '响应延迟',
      'manual': '手动调整'
    };
    return actionLabels[action] || '积分变动';
  }
  
  getLevelDescription(level) {
    const descriptions = {
      1: '法律之路的起点，继续努力！',
      2: '掌握了基础技能，稳步前进！',
      3: '经验日渐丰富，专业能力提升！',
      4: '成为专业律师，备受客户信赖！',
      5: '资深律师风范，行业内有声望！',
      6: '专家级律师，法律界的精英！',
      7: '首席律师地位，团队的领导者！',
      8: '合伙人律师，事务所的核心力量！',
      9: '高级合伙人，业界的标杆人物！',
      10: '首席合伙人，法律界的传奇！'
    };
    return descriptions[level] || '继续在法律道路上前进！';
  }
  
  getLevelRewards(level) {
    const rewards = {
      2: [
        { icon: 'star', description: '解锁客户评价系统' },
        { icon: 'bell', description: '案件通知提醒' }
      ],
      3: [
        { icon: 'chart-bar', description: '数据分析面板' },
        { icon: 'document-text', description: '高级文档模板' }
      ],
      4: [
        { icon: 'shield-check', description: '专业认证标识' },
        { icon: 'users', description: '客户管理工具' }
      ],
      5: [
        { icon: 'currency-dollar', description: '提成比例提升' },
        { icon: 'briefcase', description: '高价值案件优先' }
      ],
      6: [
        { icon: 'cog-6-tooth', description: '高级AI工具' },
        { icon: 'academic-cap', description: '专家认证徽章' }
      ],
      7: [
        { icon: 'user-group', description: '团队协作功能' },
        { icon: 'megaphone', description: '平台推广权限' }
      ],
      8: [
        { icon: 'trophy', description: '合伙人专属特权' },
        { icon: 'building-office', description: '事务所管理权限' }
      ],
      9: [
        { icon: 'fire', description: '平台推荐优先级' },
        { icon: 'globe-alt', description: '跨地区案件接入' }
      ],
      10: [
        { icon: 'star', description: '传奇律师殿堂' },
        { icon: 'crown', description: '平台终身荣誉' }
      ]
    };
    return rewards[level] || [{ icon: 'gift', description: '继续努力解锁更多奖励' }];
  }
  
  playPointsSound(isPositive) {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      if (isPositive) {
        // Positive sound - ascending notes
        oscillator.frequency.setValueAtTime(440, audioContext.currentTime); // A4
        oscillator.frequency.setValueAtTime(554.37, audioContext.currentTime + 0.1); // C#5
      } else {
        // Negative sound - descending notes
        oscillator.frequency.setValueAtTime(440, audioContext.currentTime); // A4
        oscillator.frequency.setValueAtTime(349.23, audioContext.currentTime + 0.1); // F4
      }
      
      gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
      // Ignore audio errors
    }
  }
  
  playLevelUpCelebrationSound() {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Create a more complex celebration melody
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      
      notes.forEach((frequency, index) => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime + index * 0.2);
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime + index * 0.2);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + index * 0.2 + 0.4);
        
        oscillator.start(audioContext.currentTime + index * 0.2);
        oscillator.stop(audioContext.currentTime + index * 0.2 + 0.4);
      });
    } catch (error) {
      // Ignore audio errors
    }
  }
  
  addScreenShakeEffect() {
    const body = document.body;
    body.style.animation = 'screenShake 0.5s ease-in-out';
    setTimeout(() => {
      body.style.animation = '';
    }, 500);
  }
  
  addScreenFlashEffect() {
    const flash = document.createElement('div');
    flash.className = 'screen-flash';
    flash.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: radial-gradient(circle, rgba(255,215,0,0.3) 0%, transparent 70%);
      pointer-events: none;
      z-index: 9999;
      animation: screenFlash 1s ease-out;
    `;
    
    document.body.appendChild(flash);
    
    setTimeout(() => {
      if (flash.parentNode) {
        flash.parentNode.removeChild(flash);
      }
    }, 1000);
  }
  
  triggerCelebrationEffects() {
    // Add particle effects and animations
    const container = document.querySelector('.celebration-container');
    if (container) {
      // Trigger fireworks animation
      const fireworks = container.querySelectorAll('.firework');
      fireworks.forEach((firework, index) => {
        setTimeout(() => {
          firework.style.animation = `fireworkExplode 2s ease-out ${index * 0.1}s`;
        }, index * 100);
      });
      
      // Trigger confetti animation
      const confetti = container.querySelectorAll('.confetti');
      confetti.forEach((piece, index) => {
        setTimeout(() => {
          piece.style.animation = `confettiFall 3s ease-out ${index * 0.02}s`;
        }, index * 20);
      });
    }
  }
  
  updateProgressBarAnimated() {
    const progressFill = document.querySelector('.progress-fill');
    if (!progressFill) return;
    
    const nextLevel = Math.min(this.currentLevel + 1, 10);
    const nextLevelPoints = this.levelRequirements[nextLevel];
    const currentLevelPoints = this.levelRequirements[this.currentLevel];
    const progressPoints = this.currentPoints - currentLevelPoints;
    const requiredPoints = nextLevelPoints - currentLevelPoints;
    
    const percentage = Math.min((progressPoints / requiredPoints) * 100, 100);
    
    // Enhanced animation with easing
    progressFill.style.transition = 'width 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
    requestAnimationFrame(() => {
      progressFill.style.width = `${percentage}%`;
    });
    
    // Add pulse effect for significant progress
    if (percentage > 80) {
      progressFill.style.animation = 'progressPulse 2s ease-in-out infinite';
    } else {
      progressFill.style.animation = '';
    }
  }
  
  updateMembershipMultiplier(multiplier) {
    this.membershipMultiplier = multiplier;
    this.renderLevelCard();
  }
  
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  // Public methods for manual updates
  addPoints(points, action = 'manual', multiplier = 1) {
    this.handlePointsUpdate({
      points_earned: points,
      action: action,
      multiplier_applied: multiplier
    });
  }
  
  shareAchievement(level, levelName) {
    const shareText = `🎉 我在律客平台升级到了${levelName}（等级${level}）！专业法律服务，值得信赖！`;
    const shareUrl = window.location.origin;
    
    if (navigator.share) {
      // Use native sharing if available
      navigator.share({
        title: '律客平台等级升级',
        text: shareText,
        url: shareUrl
      }).catch(err => console.log('分享失败:', err));
    } else {
      // Fallback to copying to clipboard
      navigator.clipboard.writeText(`${shareText} ${shareUrl}`).then(() => {
        this.showToast('success', '分享链接已复制', '已复制到剪贴板，可以分享给朋友了！');
      }).catch(() => {
        // Final fallback - show share modal
        this.showShareModal(shareText, shareUrl);
      });
    }
  }
  
  showShareModal(text, url) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">分享成就</h3>
          <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
            <div data-icon="x-mark" style="width: 20px; height: 20px;"></div>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">分享内容</label>
            <textarea class="form-textarea" readonly rows="3">${text} ${url}</textarea>
          </div>
          <div class="share-buttons">
            <button class="btn btn-outline" onclick="this.copyToClipboard('${text} ${url}')">
              <div data-icon="clipboard" style="width: 16px; height: 16px; margin-right: 8px;"></div>
              复制链接
            </button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Replace icons
    if (window.IconSystem) {
      const icons = modal.querySelectorAll('[data-icon]');
      icons.forEach(icon => {
        const iconName = icon.getAttribute('data-icon');
        window.IconSystem.replaceWithIcon(icon, iconName, {
          size: '20',
          className: icon.className
        });
      });
    }
    
    // Close on overlay click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }
  
  showToast(type, title, message) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div data-icon="${type === 'success' ? 'check-circle' : 'information-circle'}" class="toast-icon"></div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
      </div>
      <button class="toast-close" data-icon="x-mark"></button>
    `;
    
    // Add to container or create one
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    
    // Replace icons
    if (window.IconSystem) {
      const icons = toast.querySelectorAll('[data-icon]');
      icons.forEach(icon => {
        const iconName = icon.getAttribute('data-icon');
        window.IconSystem.replaceWithIcon(icon, iconName, {
          size: '20',
          className: icon.className
        });
      });
    }
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.remove();
      }
    }, 5000);
    
    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.remove();
    });
  }
  
  setLevel(level, points) {
    this.currentLevel = level;
    this.currentPoints = points;
    this.renderLevelCard();
    this.updateProgressBar();
  }
}

// Credits System
class CreditsSystem {
  constructor() {
    this.currentCredits = 0;
    this.weeklyCredits = 1;
    this.purchasedCredits = 0;
    this.nextResetDate = null;
    
    this.init();
  }
  
  init() {
    this.loadCreditsData();
    this.bindEvents();
  }
  
  bindEvents() {
    // Purchase button
    const purchaseButton = document.querySelector('.purchase-button');
    if (purchaseButton) {
      purchaseButton.addEventListener('click', () => {
        this.showPurchaseModal();
      });
    }
    
    // Listen for credits updates
    document.addEventListener('creditsUpdated', (event) => {
      this.updateCreditsDisplay(event.detail);
    });
  }
  
  async loadCreditsData() {
    try {
      const response = await fetch('/api/v1/credits/balance', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        this.updateCreditsDisplay(data);
      }
    } catch (error) {
      console.error('Failed to load credits data:', error);
    }
  }
  
  updateCreditsDisplay(data) {
    this.currentCredits = data.credits_remaining || 0;
    this.purchasedCredits = data.credits_purchased || 0;
    this.nextResetDate = data.next_reset_date;
    
    // Update amount display
    const amountNumber = document.querySelector('.amount-number');
    if (amountNumber) {
      amountNumber.textContent = this.currentCredits;
    }
    
    // Update info items
    const nextResetElement = document.querySelector('.info-item:first-child .info-value');
    if (nextResetElement && this.nextResetDate) {
      const resetDate = new Date(this.nextResetDate);
      nextResetElement.textContent = resetDate.toLocaleDateString('zh-CN');
    }
    
    const purchasedElement = document.querySelector('.info-item:last-child .info-value');
    if (purchasedElement) {
      purchasedElement.textContent = this.purchasedCredits;
    }
  }
  
  showPurchaseModal() {
    // Create purchase modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">购买 Credits</h3>
          <button class="modal-close" data-icon="x-mark"></button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">购买数量</label>
            <select class="form-select" id="credits-quantity">
              <option value="1">1 Credit - ¥50</option>
              <option value="5">5 Credits - ¥250</option>
              <option value="10">10 Credits - ¥500</option>
              <option value="20">20 Credits - ¥1000</option>
            </select>
          </div>
          <div class="alert alert-info">
            <div data-icon="information-circle" class="alert-icon"></div>
            <div class="alert-content">
              <div class="alert-message">
                Credits用于批量任务上传，每次批量上传消耗1个Credit，无论上传多少条记录。
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">
            取消
          </button>
          <button class="btn btn-primary" onclick="creditsSystem.processPurchase()">
            确认购买
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Replace icons
    if (window.IconSystem) {
      const icons = modal.querySelectorAll('[data-icon]');
      icons.forEach(icon => {
        const iconName = icon.getAttribute('data-icon');
        window.IconSystem.replaceWithIcon(icon, iconName, {
          size: '20',
          className: icon.className
        });
      });
    }
    
    // Close on overlay click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }
  
  async processPurchase() {
    const quantitySelect = document.getElementById('credits-quantity');
    const quantity = parseInt(quantitySelect.value);
    const amount = quantity * 50;
    
    try {
      const response = await fetch('/api/v1/credits/purchase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          credits_count: quantity
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Close modal
        document.querySelector('.modal-overlay').remove();
        
        // Show success message
        this.showToast('success', '购买成功', `成功购买 ${quantity} Credits`);
        
        // Reload credits data
        this.loadCreditsData();
      } else {
        const error = await response.json();
        this.showToast('error', '购买失败', error.detail || '请稍后重试');
      }
    } catch (error) {
      console.error('Purchase failed:', error);
      this.showToast('error', '购买失败', '网络错误，请稍后重试');
    }
  }
  
  showToast(type, title, message) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div data-icon="${type === 'success' ? 'check-circle' : 'x-circle'}" class="toast-icon"></div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
      </div>
      <button class="toast-close" data-icon="x-mark"></button>
    `;
    
    // Add to container or create one
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    
    // Replace icons
    if (window.IconSystem) {
      const icons = toast.querySelectorAll('[data-icon]');
      icons.forEach(icon => {
        const iconName = icon.getAttribute('data-icon');
        window.IconSystem.replaceWithIcon(icon, iconName, {
          size: '20',
          className: icon.className
        });
      });
    }
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.remove();
      }
    }, 5000);
    
    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.remove();
    });
  }
}

// Initialize systems when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize gamification system
  if (document.querySelector('.lawyer-level-card')) {
    window.gamificationSystem = new GamificationSystem();
  }
  
  // Initialize credits system
  if (document.querySelector('.credits-balance-card')) {
    window.creditsSystem = new CreditsSystem();
  }
});

// Enhanced floating points and celebration animations CSS
const enhancedAnimationsCSS = `
/* Enhanced Points Animation */
.floating-points-enhanced {
  position: fixed;
  pointer-events: none;
  z-index: 1000;
}

.points-burst {
  text-align: center;
  font-weight: bold;
  position: relative;
}

.points-burst .points-value {
  font-size: 2rem;
  margin-bottom: 0.25rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.points-positive {
  color: #10b981;
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

.points-negative {
  color: #ef4444;
  text-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}

.points-multiplier {
  font-size: 0.875rem;
  color: #f59e0b;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.points-action-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.points-particles {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #fbbf24;
  border-radius: 50%;
}

.particle-0 { top: -20px; left: -20px; }
.particle-1 { top: -20px; right: -20px; }
.particle-2 { bottom: -20px; left: -20px; }
.particle-3 { bottom: -20px; right: -20px; }
.particle-4 { top: -30px; left: 0; }
.particle-5 { bottom: -30px; left: 0; }
.particle-6 { top: 0; left: -30px; }
.particle-7 { top: 0; right: -30px; }

@keyframes pointsBurst {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }
  20% {
    transform: scale(1.3);
    opacity: 1;
  }
  40% {
    transform: scale(1) translateY(-10px);
    opacity: 1;
  }
  100% {
    transform: scale(0.8) translateY(-80px);
    opacity: 0;
  }
}

.particle {
  animation: particleExplode 2s ease-out forwards;
}

@keyframes particleExplode {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  50% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(0);
    opacity: 0;
  }
}

/* Enhanced Level Up Celebration */
.level-up-celebration-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: overlayFadeIn 0.5s ease-out;
}

.celebration-container {
  position: relative;
  max-width: 500px;
  width: 90%;
}

.celebration-main {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 24px;
  padding: 3rem;
  text-align: center;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  animation: celebrationBounce 1s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  overflow: hidden;
}

.celebration-main::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #f59e0b);
}

.celebration-icon-container {
  position: relative;
  margin-bottom: 2rem;
}

.celebration-icon {
  width: 80px;
  height: 80px;
  color: #f59e0b;
  margin: 0 auto;
  animation: celebrationIconPulse 2s ease-in-out infinite;
}

.celebration-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  animation: celebrationGlow 2s ease-in-out infinite alternate;
}

.celebration-title {
  font-size: 2rem;
  font-weight: 800;
  color: #1f2937;
  margin-bottom: 1rem;
  animation: celebrationTextSlide 0.8s ease-out 0.3s both;
}

.celebration-level {
  font-size: 1.5rem;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 0.5rem;
  animation: celebrationTextSlide 0.8s ease-out 0.4s both;
}

.celebration-level-number {
  font-size: 1.125rem;
  color: #6b7280;
  margin-bottom: 1rem;
  animation: celebrationTextSlide 0.8s ease-out 0.5s both;
}

.celebration-description {
  font-size: 1rem;
  color: #4b5563;
  margin-bottom: 2rem;
  animation: celebrationTextSlide 0.8s ease-out 0.6s both;
}

.celebration-rewards {
  background: #f8fafc;
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  animation: celebrationTextSlide 0.8s ease-out 0.7s both;
}

.rewards-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
}

.rewards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.reward-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: #4b5563;
}

.reward-icon {
  width: 20px;
  height: 20px;
  color: #10b981;
  flex-shrink: 0;
}

.celebration-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  animation: celebrationTextSlide 0.8s ease-out 0.8s both;
}

.celebration-continue {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border: none;
  color: white;
  padding: 0.75rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.celebration-continue:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(59, 130, 246, 0.4);
}

.celebration-share {
  background: white;
  border: 2px solid #e5e7eb;
  color: #4b5563;
  padding: 0.75rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.celebration-share:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

/* Fireworks */
.celebration-fireworks {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.firework {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #fbbf24;
  border-radius: 50%;
}

.firework-0 { top: 20%; left: 10%; }
.firework-1 { top: 30%; right: 15%; }
.firework-2 { top: 40%; left: 20%; }
.firework-3 { top: 25%; right: 25%; }
.firework-4 { top: 60%; left: 15%; }
.firework-5 { top: 70%; right: 20%; }
.firework-6 { top: 15%; left: 50%; }
.firework-7 { top: 80%; left: 45%; }
.firework-8 { top: 35%; right: 10%; }
.firework-9 { top: 55%; right: 30%; }
.firework-10 { top: 75%; left: 30%; }
.firework-11 { top: 45%; right: 40%; }

@keyframes fireworkExplode {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  50% {
    transform: scale(3);
    opacity: 1;
  }
  100% {
    transform: scale(6);
    opacity: 0;
  }
}

/* Confetti */
.celebration-confetti {
  position: absolute;
  top: -50px;
  left: 0;
  right: 0;
  height: 100vh;
  pointer-events: none;
  overflow: hidden;
}

.confetti {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.confetti-0 { background: #ef4444; }
.confetti-1 { background: #3b82f6; }
.confetti-2 { background: #10b981; }
.confetti-3 { background: #f59e0b; }
.confetti-4 { background: #8b5cf6; }

@keyframes confettiFall {
  0% {
    transform: translateY(-100vh) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(100vh) rotate(720deg);
    opacity: 0;
  }
}

/* Screen Effects */
@keyframes screenShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
  20%, 40%, 60%, 80% { transform: translateX(2px); }
}

@keyframes screenFlash {
  0% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}

/* Progress Bar Enhancement */
@keyframes progressPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
  50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
}

/* Base Animations */
@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes celebrationBounce {
  0% {
    opacity: 0;
    transform: scale(0.3) translateY(100px);
  }
  50% {
    opacity: 1;
    transform: scale(1.05) translateY(-10px);
  }
  70% {
    transform: scale(0.95) translateY(5px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes celebrationIconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes celebrationGlow {
  0% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); }
  100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1.2); }
}

@keyframes celebrationTextSlide {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 640px) {
  .celebration-main {
    padding: 2rem;
    margin: 1rem;
  }
  
  .celebration-title {
    font-size: 1.5rem;
  }
  
  .celebration-level {
    font-size: 1.25rem;
  }
  
  .celebration-icon {
    width: 60px;
    height: 60px;
  }
  
  .celebration-actions {
    flex-direction: column;
  }
}
`;

// Inject CSS
const style = document.createElement('style');
style.textContent = enhancedAnimationsCSS;
document.head.appendChild(style);

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GamificationSystem, CreditsSystem };
}