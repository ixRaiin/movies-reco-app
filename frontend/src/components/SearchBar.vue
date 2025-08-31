<template>
  <div class="search-container">
    <input
      v-model="query"
      @keyup.enter="handleSearch"
      placeholder="What mood are you in?"
      class="search-input"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits } from "vue";
import { useRouter } from "vue-router";

const query = ref("");
const emit = defineEmits(["search"]);

const handleSearch = async () => {
  try {
    const response = await fetch(`/api/mood/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: query.value }),
    });
    
    if (response.ok) {
      const data = await response.json();
      emit("search", data.movies); // Send the movie data to parent component
    } else {
      console.error("Error fetching movie recommendations");
    }
  } catch (error) {
    console.error("Error:", error);
  }
};
</script>

<style scoped>
.search-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.search-input {
  padding: 10px;
  font-size: 16px;
  width: 80%;
  max-width: 600px;
  border-radius: 8px;
  border: 1px solid #ccc;
  outline: none;
}

.search-input:focus {
  border-color: #0077cc;
}
</style>
