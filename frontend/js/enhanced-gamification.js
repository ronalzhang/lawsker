/**
 * Enhanced Gamification System for Lawsker
 * Advanced lawyer progression, achievements, and visual feedback
 */

class EnhancedGamificationSystem {
  constructor() {
    this.currentLevel = 1;
    this.currentPoints = 0;
    this.membershipMultiplier = 1;
    this.achievements = new Map();
    this.levelThresholds = [
      { level: 1, points: 0, title: '见习律师', description: '刚刚起步的法律新人' },
      { level: 2, points: 500, title: '初级律师', description: '掌握基础法律技能' },
      { level: 3, points: 1500, title: '中级律师', description: '具备丰富实践经验' },
      { level: 4, points: 3000, title: '高级律师', description: '专业领域的专家' },
      { level: 5, points: 5000, title: '资深律师', description: '行业内的权威人士' },
      { level: 6, points: 8000, title: '专家律师', description: '法律界的精英' },
      { level: 7, points: 12000, title: '首席律师', description: '团队的领导者' },
      { level: 8, points: 18000, title: '合伙人律师', description: '事务所的核心力量' },
      { level: 9, points: 25000, title: '高级合伙人', description: '业界的标杆人物' },
      { level: 10, points: 35000, title: '首席合伙人', description: '法律界的传奇' }
    ];
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.initializeAchievements();
    this.loadUserProgress();
  }

  setupEventListeners() {
    // Listen for point changes
    document.addEventListener('pointsChanged', (e) => {
      this.handlePointsChange(e.detail);
    });

    // Listen for level changes
    document.addEventListener('levelChanged', (e) => {
      this.handleLevelChange(e.detail);
    });

    // Listen for achievement unlocks
    document.addEventListener('achievementUnlocked', (e) => {
      this.handleAchievementUnlock(e.detail);
    });
  }

  initializeAchievements() {
    const achievements = [
      {
        id: 'first_case',
        title: '初次出击',
        description: '完成第一个案件',
        icon: 'scale',
        condition: (stats) => stats.casesCompleted >= 1
      },
      {
        id: 'perfect_rating',
        title: '完美评价',
        description: '获得第一个5星评价',
        icon: 'star',
        condition: (stats) => stats.fiveStarRatings >= 1
      },
      {
        id: 'speed_demon',
        title: '闪电响应',
        description: '1小时内响应案件',
        icon: 'clock',
        condition: (stats) => stats.fastResponses >= 1
      },
      {
        id: 'case_master',
        title: '案件大师',
        description: '完成100个案件',
        icon: 'briefcase',
        condition: (stats) => stats.casesCompleted >= 100
      },
      {
        id: 'point_collector',
        title: '积分收集者',
        description: '累计获得10000积分',
        icon: 'trophy',
        condition: (stats) => stats.totalPoints >= 10000
      },
      {
        id: 'ai_expert',
        title: 'AI专家',
        description: '使用AI工具500次',
        icon: 'cog-6-tooth',
        condition: (stats) => stats.aiUsage >= 500
      }
    ];

    achievements.forEach(achievement => {
      this.achievements.set(achievement.id, {
        ...achievement,
        unlocked: false,
        unlockedAt: null
      });
    });
  }

  loadUserProgress() {
    // Load from localStorage or API
    const savedProgress = localStorage.getItem('lawyerProgress');
    if (savedProgress) {
      const progress = JSON.parse(savedProgress);
      this.currentLevel = progress.level || 1;
      this.currentPoints = progress.points || 0;
      this.membershipMultiplier = progress.multiplier || 1;
      
      // Load achievements
      if (progress.achievements) {
        progress.achievements.forEach(achievementData => {
          if (this.achievements.has(achievementData.id)) {
            this.achievements.set(achievementData.id, {
              ...this.achievements.get(achievementData.id),
              ...achievementData
            });
          }
        });
      }
    }
  }

  saveUserProgress() {
    const progress = {
      level: this.currentLevel,
      points: this.currentPoints,
      multiplier: this.membershipMultiplier,
      achievements: Array.from(this.achievements.values())
    };
    localStorage.setItem('lawyerProgress', JSON.stringify(progress));
  }

  // Points Management
  addPoints(basePoints, action, multiplier = null) {
    const effectiveMultiplier = multiplier || this.membershipMultiplier;
    const finalPoints = Math.floor(basePoints * effectiveMultiplier);
    
    this.currentPoints += finalPoints;
    
    // Show points animation
    this.showPointsAnimation(finalPoints, action);
    
    // Check for level up
    this.checkLevelUp();
    
    // Update UI
    this.updateProgressDisplay();
    
    // Save progress
    this.saveUserProgress();
    
    // Dispatch event
    document.dispatchEvent(new CustomEvent('pointsChanged', {
      detail: {
        points: finalPoints,
        total: this.currentPoints,
        action: action,
        multiplier: effectiveMultiplier
      }
    }));

    return finalPoints;
  }

  showPointsAnimation(points, action) {
    const animation = document.createElement('div');
    animation.className = 'points-animation';
    animation.textContent = `+${points} 积分`;
    
    // Position near the action element or center of screen
    const actionElement = document.querySelector(`[data-action="${action}"]`) || 
                         document.querySelector('.lawyer-level-system') ||
                         document.body;
    
    const rect = actionElement.getBoundingClientRect();
    animation.style.left = (rect.left + rect.width / 2) + 'px';
    animation.style.top = (rect.top + rect.height / 2) + 'px';
    
    document.body.appendChild(animation);
    
    // Remove after animation
    setTimeout(() => {
      if (animation.parentNode) {
        animation.parentNode.removeChild(animation);
      }
    }, 2000);
  }

  checkLevelUp() {
    const newLevel = this.calculateLevel(this.currentPoints);
    if (newLevel > this.currentLevel) {
      const oldLevel = this.currentLevel;
      this.currentLevel = newLevel;
      this.showLevelUpCelebration(oldLevel, newLevel);
      
      document.dispatchEvent(new CustomEvent('levelChanged', {
        detail: {
          oldLevel: oldLevel,
          newLevel: newLevel,
          points: this.currentPoints
        }
      }));
    }
  }

  calculateLevel(points) {
    for (let i = this.levelThresholds.length - 1; i >= 0; i--) {
      if (points >= this.levelThresholds[i].points) {
        return this.levelThresholds[i].level;
      }
    }
    return 1;
  }

  showLevelUpCelebration(oldLevel, newLevel) {
    const levelData = this.levelThresholds.find(l => l.level === newLevel);
    const rewards = this.getLevelRewards(newLevel);
    
    const overlay = document.createElement('div');
    overlay.className = 'level-up-overlay';
    
    overlay.innerHTML = `
      <div class="level-up-celebration">
        <div class="celebration-icon">
          <div data-icon="trophy" style="width: 40px; height: 40px;"></div>
        </div>
        <h2 class="celebration-title">恭喜升级！</h2>
        <p class="celebration-message">
          您已升级至 <strong>${levelData.title}</strong> (等级 ${newLevel})
        </p>
        <div class="celebration-rewards">
          <h4>解锁奖励</h4>
          <div class="rewards-list">
            ${rewards.map(reward => `
              <div class="reward-item">
                <div class="reward-icon" data-icon="${reward.icon}"></div>
                <span>${reward.description}</span>
              </div>
            `).join('')}
          </div>
        </div>
        <button class="btn btn-primary" onclick="this.parentElement.parentElement.remove()">
          继续前进
        </button>
      </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Initialize icons
    if (window.IconSystem) {
      window.IconSystem.initializeCharts();
    }
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
      if (overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
      }
    }, 10000);
  }

  getLevelRewards(level) {
    const rewards = [];
    
    switch (level) {
      case 2:
        rewards.push({ icon: 'star', description: '解锁客户评价系统' });
        break;
      case 3:
        rewards.push({ icon: 'chart-bar', description: '解锁数据分析面板' });
        rewards.push({ icon: 'bell', description: '优先案件通知' });
        break;
      case 4:
        rewards.push({ icon: 'shield-check', description: '专业认证标识' });
        break;
      case 5:
        rewards.push({ icon: 'user-group', description: '团队协作功能' });
        rewards.push({ icon: 'currency-dollar', description: '提成比例提升' });
        break;
      case 6:
        rewards.push({ icon: 'briefcase', description: '高价值案件优先权' });
        break;
      case 7:
        rewards.push({ icon: 'cog-6-tooth', description: '高级AI工具访问' });
        break;
      case 8:
        rewards.push({ icon: 'trophy', description: '合伙人专属特权' });
        break;
      case 9:
        rewards.push({ icon: 'fire', description: '平台推荐优先级' });
        break;
      case 10:
        rewards.push({ icon: 'star', description: '传奇律师殿堂' });
        break;
    }
    
    return rewards;
  }

  // UI Update Methods
  updateProgressDisplay() {
    const containers = document.querySelectorAll('.lawyer-level-system');
    containers.forEach(container => {
      this.renderLevelSystem(container);
    });
  }

  renderLevelSystem(container) {
    const currentLevelData = this.levelThresholds.find(l => l.level === this.currentLevel);
    const nextLevelData = this.levelThresholds.find(l => l.level === this.currentLevel + 1);
    
    const currentLevelPoints = currentLevelData.points;
    const nextLevelPoints = nextLevelData ? nextLevelData.points : currentLevelPoints;
    const progressPoints = this.currentPoints - currentLevelPoints;
    const requiredPoints = nextLevelPoints - currentLevelPoints;
    const progressPercentage = nextLevelData ? (progressPoints / requiredPoints) * 100 : 100;
    
    container.innerHTML = `
      <div class="level-header">
        <div class="level-badge">
          <div class="level-icon level-${this.currentLevel}">
            ${this.currentLevel}
          </div>
          <div class="level-info">
            <div class="level-title">${currentLevelData.title}</div>
            <div class="level-subtitle">${currentLevelData.description}</div>
          </div>
        </div>
        ${this.membershipMultiplier > 1 ? `
          <div class="membership-multiplier">
            <div data-icon="star" style="width: 16px; height: 16px;"></div>
            <span>${this.membershipMultiplier}x 积分倍数</span>
          </div>
        ` : ''}
      </div>
      
      <div class="level-progress">
        <div class="progress-header">
          <div class="progress-label">
            ${nextLevelData ? `距离 ${nextLevelData.title}` : '已达最高等级'}
          </div>
          <div class="progress-points">
            ${this.currentPoints.toLocaleString()} 积分
            ${nextLevelData ? ` / ${nextLevelPoints.toLocaleString()}` : ''}
          </div>
        </div>
        
        <div class="progress-bar-container">
          <div class="progress-bar-fill" style="width: ${progressPercentage}%"></div>
        </div>
        
        ${this.renderProgressMilestones()}
      </div>
      
      ${this.renderAchievements()}
    `;
    
    // Initialize icons
    if (window.IconSystem) {
      setTimeout(() => window.IconSystem.initializeCharts(), 100);
    }
  }

  renderProgressMilestones() {
    const milestones = [];
    const startLevel = Math.max(1, this.currentLevel - 2);
    const endLevel = Math.min(10, this.currentLevel + 2);
    
    for (let i = startLevel; i <= endLevel; i++) {
      const levelData = this.levelThresholds.find(l => l.level === i);
      let status = 'future';
      
      if (i < this.currentLevel) status = 'completed';
      else if (i === this.currentLevel) status = 'current';
      
      milestones.push(`
        <div class="milestone ${status}">
          <div class="milestone-dot"></div>
          <div class="milestone-label">L${i}</div>
        </div>
      `);
    }
    
    return `
      <div class="progress-milestones">
        ${milestones.join('')}
      </div>
    `;
  }

  renderAchievements() {
    const achievementsList = Array.from(this.achievements.values());
    const achievementsHTML = achievementsList.map(achievement => `
      <div class="achievement-badge ${achievement.unlocked ? 'unlocked' : 'locked'}">
        <div class="achievement-icon">
          <div data-icon="${achievement.icon}" style="width: 24px; height: 24px;"></div>
        </div>
        <div class="achievement-title">${achievement.title}</div>
        <div class="achievement-description">${achievement.description}</div>
      </div>
    `).join('');
    
    return `
      <div class="achievements-section">
        <h3 class="text-lg font-semibold text-primary mb-4">成就徽章</h3>
        <div class="achievements-grid">
          ${achievementsHTML}
        </div>
      </div>
    `;
  }

  // Achievement System
  checkAchievements(userStats) {
    this.achievements.forEach((achievement, id) => {
      if (!achievement.unlocked && achievement.condition(userStats)) {
        this.unlockAchievement(id);
      }
    });
  }

  unlockAchievement(achievementId) {
    const achievement = this.achievements.get(achievementId);
    if (achievement && !achievement.unlocked) {
      achievement.unlocked = true;
      achievement.unlockedAt = new Date().toISOString();
      
      this.showAchievementNotification(achievement);
      this.saveUserProgress();
      
      document.dispatchEvent(new CustomEvent('achievementUnlocked', {
        detail: achievement
      }));
    }
  }

  showAchievementNotification(achievement) {
    // Create toast notification for achievement
    if (window.showToast) {
      window.showToast({
        type: 'success',
        title: '成就解锁！',
        message: `您获得了"${achievement.title}"成就`,
        duration: 5000
      });
    }
  }

  // Credits System Enhancement
  renderCreditsCard(container, creditsData) {
    const { balance = 0, weeklyReset = 7, purchased = 0 } = creditsData;
    
    container.innerHTML = `
      <div class="credits-card-enhanced">
        <div class="credits-header">
          <div class="credits-icon">
            <div data-icon="credit-card" style="width: 24px; height: 24px;"></div>
          </div>
          <div class="text-sm opacity-90">Credits 余额</div>
        </div>
        
        <div class="credits-balance">${balance}</div>
        <div class="credits-label">可用 Credits</div>
        
        <div class="credits-actions">
          <button class="credits-btn" onclick="purchaseCredits()">
            <div data-icon="plus" style="width: 16px; height: 16px; display: inline-block; margin-right: 4px;"></div>
            购买
          </button>
          <button class="credits-btn" onclick="viewCreditsHistory()">
            <div data-icon="clock" style="width: 16px; height: 16px; display: inline-block; margin-right: 4px;"></div>
            历史
          </button>
        </div>
        
        <div class="text-xs opacity-75 mt-3">
          ${weeklyReset} 天后重置 | 已购买 ${purchased} 个
        </div>
      </div>
    `;
    
    // Initialize icons
    if (window.IconSystem) {
      setTimeout(() => window.IconSystem.initializeCharts(), 100);
    }
  }

  // Demo Mode Indicators
  enableDemoMode() {
    // Add demo indicator
    if (!document.querySelector('.demo-mode-indicator')) {
      const indicator = document.createElement('div');
      indicator.className = 'demo-mode-indicator';
      indicator.innerHTML = `
        <div data-icon="eye" style="width: 16px; height: 16px; display: inline-block; margin-right: 4px;"></div>
        演示模式
      `;
      document.body.appendChild(indicator);
    }
    
    // Add demo overlays to cards
    document.querySelectorAll('.card, .stat-card').forEach(card => {
      if (!card.classList.contains('demo-overlay')) {
        card.classList.add('demo-overlay');
      }
    });
  }

  disableDemoMode() {
    // Remove demo indicator
    const indicator = document.querySelector('.demo-mode-indicator');
    if (indicator) {
      indicator.remove();
    }
    
    // Remove demo overlays
    document.querySelectorAll('.demo-overlay').forEach(card => {
      card.classList.remove('demo-overlay');
    });
  }

  // Public API Methods
  setLevel(level, points) {
    this.currentLevel = level;
    this.currentPoints = points;
    this.updateProgressDisplay();
    this.saveUserProgress();
  }

  setMembershipMultiplier(multiplier) {
    this.membershipMultiplier = multiplier;
    this.updateProgressDisplay();
    this.saveUserProgress();
  }

  getCurrentLevel() {
    return this.currentLevel;
  }

  getCurrentPoints() {
    return this.currentPoints;
  }

  getAchievements() {
    return Array.from(this.achievements.values());
  }

  // Event Handlers
  handlePointsChange(detail) {
    // Additional logic for points change
    console.log('Points changed:', detail);
  }

  handleLevelChange(detail) {
    // Additional logic for level change
    console.log('Level changed:', detail);
  }

  handleAchievementUnlock(detail) {
    // Additional logic for achievement unlock
    console.log('Achievement unlocked:', detail);
  }
}

// Initialize global instance
window.EnhancedGamificationSystem = new EnhancedGamificationSystem();

// Convenience functions
window.addLawyerPoints = (points, action, multiplier) => {
  return window.EnhancedGamificationSystem.addPoints(points, action, multiplier);
};

window.setLawyerLevel = (level, points) => {
  window.EnhancedGamificationSystem.setLevel(level, points);
};

window.enableDemoMode = () => {
  window.EnhancedGamificationSystem.enableDemoMode();
};

window.disableDemoMode = () => {
  window.EnhancedGamificationSystem.disableDemoMode();
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = EnhancedGamificationSystem;
}