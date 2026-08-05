<script setup lang="ts">

import { welcomeQuestionGroups } from '@/data/assistant.mock'



defineProps<{

  questions: string[]

}>()



const emit = defineEmits<{

  (e: 'question-click', question: string): void

}>()

</script>



<template>

  <div class="welcome-area">

    <div class="welcome-content">

      <h2 class="welcome-title">今天需要掌握哪类项目状态？</h2>

      <p class="welcome-desc">

        高速项目 ESG 管理助手：先给状态判断，再给风险、依据与下一步建议；上级检查类同答可下载合规资料包。

      </p>



      <div class="suggestions">

        <div class="suggestions-title">推荐业务问题</div>

        <div

          v-for="group in welcomeQuestionGroups"

          :key="group.group"

          class="suggestion-group"

        >

          <div class="group-label">{{ group.group }}</div>

          <div class="suggestion-list">

            <div

              v-for="(q, idx) in group.questions"

              :key="idx"

              class="suggestion-item"

              @click="emit('question-click', q)"

            >

              <span class="suggestion-text">{{ q }}</span>

              <span class="suggestion-arrow">→</span>

            </div>

          </div>

        </div>

      </div>

    </div>

  </div>

</template>



<style scoped lang="scss">

@use '@/styles/tokens.scss' as *;



.welcome-area {

  width: 100%;

  padding-top: 12px;

}



.welcome-content {

  max-width: 820px;

  margin: 0 auto;

  text-align: left;

}



.welcome-title {

  margin: 0 0 12px;

  font-size: 30px;

  font-weight: 700;

  color: var(--text-primary);

  letter-spacing: -0.01em;

}



.welcome-desc {

  margin: 0 0 28px;

  font-size: 14px;

  line-height: 1.6;

  color: var(--text-tertiary);

}



.suggestions-title {

  font-size: 14px;

  font-weight: 600;

  color: var(--text-secondary);

  margin-bottom: 14px;

}



.suggestion-group {

  margin-bottom: 16px;

}



.group-label {

  font-size: 12px;

  font-weight: 700;

  letter-spacing: 0.08em;

  color: var(--cyan);

  margin-bottom: 8px;

}



.suggestion-list {

  display: flex;

  flex-direction: column;

  gap: 8px;

}



.suggestion-item {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 14px 18px;

  background: rgba(8, 40, 69, 0.65);

  border: 1px solid rgba(74, 147, 207, 0.18);

  border-radius: var(--radius-md);

  cursor: pointer;

  transition: all 0.2s ease;



  &:hover {

    background: rgba(12, 50, 84, 0.82);

    border-color: rgba(74, 147, 207, 0.32);



    .suggestion-arrow {

      transform: translateX(4px);

      color: var(--cyan);

    }

  }

}



.suggestion-text {

  flex: 1;

  font-size: 14px;

  color: var(--text-primary);

  line-height: 1.4;

}



.suggestion-arrow {

  color: var(--text-tertiary);

  font-size: 14px;

  flex-shrink: 0;

  transition: all 0.2s ease;

}



@media (max-width: 1600px) {

  .welcome-title {

    font-size: 26px;

  }

}

</style>


